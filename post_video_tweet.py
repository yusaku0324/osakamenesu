import csv
import json
import random
import time
import logging
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

# Custom module imports
try:
    from bot.services.twitter_client.driver_factory import create_driver
    from bot.services.twitter_client.cookie_loader import load_cookies
    from bot.services.twitter_client.poster import post_to_twitter
    from bot.utils.log import setup_logger
except ImportError as e:
    print(f"Error importing bot modules: {e}. Ensure 'bot' directory is in PYTHONPATH or script is run from project root.")
    # Fallback basic logger if setup_logger fails
    logger = logging.getLogger("video_tweeter_fallback")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.warning("Using fallback basic logging due to import error.")
    # To make the script runnable for testing even if bot modules are missing, define stubs
    # This is NOT for production but helps in isolated script development/testing.
    if "create_driver" not in globals():
        def create_driver(headless):
            logger.error("STUB: create_driver called! Bot modules not loaded.")
            raise NotImplementedError("create_driver stub called")
    if "load_cookies" not in globals():
        def load_cookies(driver, path):
            logger.error("STUB: load_cookies called! Bot modules not loaded.")
            return False # Simulate failure
    if "post_to_twitter" not in globals():
        def post_to_twitter(driver, post_text, media_files, logger):
            logger.error("STUB: post_to_twitter called! Bot modules not loaded.")
            return None # Simulate failure
else:
    logger = setup_logger("video_tweeter", "video_tweeter.log")

# --- Constants and Configuration ---
QUESTIONS_TSV_PATH = Path("questions.tsv")
VIDEO_MAP_CSV_PATH = Path("video_question_map.csv")
# POSTED_LOG_PATH will be dynamic
# COOKIE_FILE_PATH will be dynamic
# TARGET_ACCOUNT_NAME will be dynamic
COMMON_HASHTAGS = "京都 祇園 水商売 キャバクラ クラブ スカウト 関西 大阪 木屋町 未経験"
HEADLESS_BROWSER = True # Default, can be overridden by --debug

# --- Helper Functions ---

def load_questions_and_answers(filepath: Path) -> Dict[str, str]:
    """Loads Q&A from a TSV file (Question\tAnswer)."""
    qa_map = {}
    if not filepath.exists():
        logger.error(f"Questions TSV file not found: {filepath}")
        return qa_map
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for i, row in enumerate(reader):
            if len(row) == 2:
                question_raw, answer_raw = row[0], row[1]
                question = " ".join(question_raw.strip().split())
                answer = answer_raw.strip()
                if question:
                    qa_map[question] = answer
            else:
                logger.warning(f"Skipping malformed row {i+1} in {filepath}: {row}")
    logger.info(f"Loaded {len(qa_map)} Q&A pairs from {filepath}")
    return qa_map

def load_video_map(filepath: Path) -> Dict[str, str]:
    """Loads video map from a CSV file (question,video_path)."""
    video_map = {}
    if not filepath.exists():
        logger.error(f"Video map CSV file not found: {filepath}")
        return video_map
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_raw = row.get("question")
            video_path_raw = row.get("video_path")
            if question_raw and video_path_raw:
                question = " ".join(question_raw.strip().split())
                video_path = video_path_raw.strip()
                video_map[question] = video_path
            else:
                logger.warning(f"Skipping row with missing data in {filepath}: {row}")
    logger.info(f"Loaded {len(video_map)} video mappings from {filepath}")
    return video_map

def load_posted_log(filepath: Path) -> Set[str]:
    """Loads the set of already posted questions (one question per line)."""
    posted_questions = set()
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                posted_questions.add(" ".join(line.strip().split()))
    logger.info(f"Loaded {len(posted_questions)} posted items from {filepath}")
    return posted_questions

def append_to_posted_log(filepath: Path, question_text: str):
    """Appends a question to the log of posted items."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    normalized_question_text = " ".join(question_text.strip().split())
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{normalized_question_text}\n")
    logger.info(f"Logged as posted: {normalized_question_text[:50]}... to {filepath}")

def select_item_to_post(
    qa_data: Dict[str, str],
    video_map: Dict[str, str],
    posted_log: Set[str]
) -> Optional[Dict[str, str]]:
    """
    Selects an item to post. Prioritizes unposted items.
    Returns a dictionary with 'question', 'answer', 'video_path' or None.
    """
    available_items = []
    for q_text_key, answer_text in qa_data.items():
        normalized_q_key = " ".join(q_text_key.strip().split()) # Key in qa_data is already normalized by load_questions_and_answers
        if normalized_q_key in video_map:
            available_items.append({
                "question": normalized_q_key,
                "answer": answer_text,
                "video_path": video_map[normalized_q_key]
            })
        else:
            logger.warning(f"Question '{normalized_q_key[:50]}...' found in Q&A but not in video map. Skipping.")

    if not available_items:
        logger.warning("No items available for posting (Q&A and video map yielded no combined items).")
        return None

    unposted_items = [item for item in available_items if item["question"] not in posted_log]
    
    selected_item = None
    if unposted_items:
        logger.info(f"{len(unposted_items)} unposted items available. Selecting one randomly.")
        selected_item = random.choice(unposted_items)
    elif available_items:
        logger.info("All available items have been posted before. Selecting one randomly from all items.")
        selected_item = random.choice(available_items)
    else:
        logger.warning("No items to select for posting.")
        return None
        
    if selected_item:
        logger.info(f"Selected item to post: {selected_item['question'][:50]}...")
    return selected_item

async def main_post_video_tweet(account_id: str, headless_mode: bool):
    cookie_file_path = Path(f"cookies/{account_id}_twitter_cookies.json")
    posted_log_path = Path(f"logs/posted_video_tweets_{account_id}.log")
    target_account_name_for_log = f"@{account_id}"

    logger.info(f"--- Starting Video Tweet Posting Script for account: {target_account_name_for_log} ---")
    logger.info(f"Using cookie file: {cookie_file_path}")
    logger.info(f"Using posted log: {posted_log_path}")

    qa_data = load_questions_and_answers(QUESTIONS_TSV_PATH)
    video_map = load_video_map(VIDEO_MAP_CSV_PATH)
    posted_log = load_posted_log(posted_log_path)

    if not qa_data or not video_map:
        logger.error("Essential data (Q&A or Video Map) could not be loaded. Exiting.")
        return

    item_to_post = select_item_to_post(qa_data, video_map, posted_log)

    if not item_to_post:
        logger.info("No item selected for posting. Exiting.")
        return

    tweet_text = f"{item_to_post['answer']}\n\n{COMMON_HASHTAGS}"
    video_file_path = item_to_post['video_path']
    question_for_log = item_to_post['question']

    logger.info(f"Attempting to post for {target_account_name_for_log}: Video='{video_file_path}', Text='{tweet_text[:70]}...'" )

    driver = None
    try:
        if not cookie_file_path.exists():
            logger.error(f"Cookie file not found: {cookie_file_path}. Cannot proceed.")
            return
        
        logger.info(f"Creating browser driver (headless: {headless_mode})...")
        driver = create_driver(headless=headless_mode)

        logger.info(f"Loading cookies from {cookie_file_path}...")
        if not load_cookies(driver, str(cookie_file_path)):
            logger.error(f"Failed to load cookies for {target_account_name_for_log}. Aborting post.")
            return

        logger.info(f"Calling post_to_twitter for account {target_account_name_for_log}...")
        post_identifier = f"{account_id}_{question_for_log[:20].replace(' ','_')}_{int(time.time())}"
        
        tweet_url_or_id = post_to_twitter(
            driver=driver,
            post_text=tweet_text,
            media_files=[video_file_path] if video_file_path else None, 
            logger=logger 
        )

        if tweet_url_or_id:
            logger.info(f"Successfully posted for {target_account_name_for_log}! Tweet URL: {tweet_url_or_id}")
            append_to_posted_log(posted_log_path, question_for_log)
        else:
            logger.error(f"Posting failed for {target_account_name_for_log}.")

    except Exception as e:
        logger.error(f"An error occurred during the posting process for {target_account_name_for_log}: {e}")
        logger.exception("Traceback:")
    finally:
        if driver:
            logger.info(f"Closing browser driver for {target_account_name_for_log}.")
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {e}")
        logger.info(f"--- Video Tweet Posting Script Finished for account: {target_account_name_for_log} ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post a Q&A video tweet for a specific account.")
    parser.add_argument(
        "--account", 
        type=str, 
        required=True, 
        help="The account ID (e.g., cristianisraelv, menesu324) to use for posting. Affects cookie and log file paths."
    )
    args = parser.parse_args()

    Path("logs").mkdir(parents=True, exist_ok=True)
    
    asyncio.run(main_post_video_tweet(args.account, HEADLESS_BROWSER))