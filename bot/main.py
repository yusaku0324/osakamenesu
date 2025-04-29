"""
Main entry point for the bot application
"""
import os
import sys
import logging
from typing import Optional, Dict, Any

from bot.utils.log import setup_logger
from bot.services.twitter_client.poster import post_to_twitter
from bot.services.twitter_client.driver_factory import create_driver
from bot.services.twitter_client.cookie_loader import load_cookies
from bot.utils.fingerprint import PostDeduplicator

logger = setup_logger("bot_main", "bot_main.log")


def process_queue(queue_file: Optional[str] = None, qa_file: Optional[str] = None, 
                  env_vars: Optional[Dict[str, str]] = None) -> int:
    """
    Process the queue file and post to Twitter
    
    Args:
        queue_file: Path to queue file
        qa_file: Path to Q&A data file
        env_vars: Environment variables to set
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        if env_vars:
            for key, value in env_vars.items():
                os.environ[key] = value
        
        if not queue_file:
            queue_file = os.getenv("QUEUE_FILE", "queue/queue_2025-04-27.yaml")
        
        if not qa_file:
            qa_file = os.getenv("QA_FILE", "qa_sheet_polite_fixed.csv")
        
        cookie_path = os.getenv("COOKIE_PATH", "niijima_cookies.json")
        
        logger.info(f"Processing queue file: {queue_file}")
        logger.info(f"Using Q&A file: {qa_file}")
        logger.info(f"Using cookie file: {cookie_path}")
        
        deduplicator = PostDeduplicator()
        
        driver = create_driver()
        
        if not load_cookies(driver, cookie_path):
            logger.error("Failed to load cookies")
            driver.quit()
            return 1
        
        
        driver.quit()
        return 0
    
    except Exception as e:
        logger.error(f"Error processing queue: {e}")
        return 1


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot main entry point")
    parser.add_argument("--queue-file", help="Path to queue file")
    parser.add_argument("--qa-file", help="Path to Q&A data file")
    parser.add_argument("--cookie-path", help="Path to cookie file")
    
    args = parser.parse_args()
    
    if args.cookie_path:
        os.environ["COOKIE_PATH"] = args.cookie_path
    
    return process_queue(args.queue_file, args.qa_file)


if __name__ == "__main__":
    sys.exit(main())
