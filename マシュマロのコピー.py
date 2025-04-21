#!/usr/bin/env python3
import os
import sys
import time
import json
import random
import glob
import requests
import pyperclip
import pandas as pd
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# --------------------------------------------
# 共通処理：ランダム待機・絵文字生成など
# --------------------------------------------
def random_delay(min_sec=1, max_sec=3):
    """ランダムな待機時間（秒）を返す"""
    return random.uniform(min_sec, max_sec)

def get_random_emojis(n=2):
    """UTF-8の絵文字からランダムにn個選んで連結して返す"""
    emoji_list = [
        "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
        "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
        "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩",
        "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣",
        "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬",
        "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗",
        "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯",
        "😦", "😧", "😮", "😲", "😴", "🤤", "😪", "😵", "🤐", "🥴",
        "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👿",
        "👹", "👺", "🤡", "💩", "👻", "💀", "☠️", "👽", "👾", "🤖",
        "🎃"
    ]
    return ''.join(random.sample(emoji_list, n))

# --------------------------------------------
# Selenium ドライバー作成
# --------------------------------------------
def create_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.implicitly_wait(10)
    return driver

def paste_text(driver, element, text):
    pyperclip.copy(text)
    if sys.platform.startswith('darwin'):
        paste_keys = (Keys.COMMAND, 'v')
    else:
        paste_keys = (Keys.CONTROL, 'v')
    element.send_keys(*paste_keys)

# --------------------------------------------
# safe_click 関数（完全版）
# --------------------------------------------
def safe_click(driver, element, wait_time=1):
    """
    対象要素を表示領域にスクロールし、通常クリックを試み、
    それが失敗した場合は ActionChains によるクリックで再試行する。
    """
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(wait_time)
        element.click()
    except Exception as e:
        print("標準クリックでエラー: ", e)
        try:
            ActionChains(driver).move_to_element(element).click(element).perform()
        except Exception as e2:
            raise Exception("safe_click 内で再試行も失敗: " + str(e2))

# --------------------------------------------
# JSONL 読み込み（質問・回答）
# --------------------------------------------
def load_questions(jsonl_filepath):
    questions = []
    with open(jsonl_filepath, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    prompt = data.get("prompt", "")
                    question = prompt.split("->")[0].strip()
                    if question:
                        questions.append(question)
                except json.JSONDecodeError as e:
                    print("JSON エラー:", e)
    return questions

def find_answer_for_question(jsonl_filepath, question):
    """質問に部分一致する回答を検索。なければランダムに回答を返す"""
    answer = None
    answers = []
    with open(jsonl_filepath, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    prompt = data.get("prompt", "")
                    completion = data.get("completion", "").strip()
                    if question in prompt and completion:
                        answer = completion
                        break
                    if completion:
                        answers.append(completion)
                except Exception as e:
                    print("回答読み込みエラー:", e)
    if not answer and answers:
        answer = random.choice(answers)
    return answer

# --------------------------------------------
# Part1: マシュマロに匿名投稿（質問）
# --------------------------------------------
def post_question_anonymously():
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    target_url = "https://marshmallow-qa.com/a3qdqlchqhk06ug?t=3qfsdg&utm_medium=url_text&utm_source=promotion"
    questions = load_questions("/Users/yusaku/kakeru/qanda.jsonl")
    print("抽出された質問:", questions)
    random_question = random.choice(questions)
    print("選ばれた質問:", random_question)
    try:
        driver.get(target_url)
        wait = WebDriverWait(driver, 20)
        textarea = wait.until(EC.presence_of_element_located((By.ID, "message_content")))
        time.sleep(5)
        textarea.clear()
        textarea.send_keys(random_question)
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'おくる')]")))
        safe_click(driver, submit_button)
        time.sleep(7)
        print("匿名の質問投稿完了。")
        try:
            extra_submit_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='submit' and contains(normalize-space(.), 'おくる')]")
            ))
            safe_click(driver, extra_submit_button)
            time.sleep(7)
            print("追加の「おくる」ボタンもクリックされました。")
        except Exception as extra_error:
            print("追加送信ボタンでエラー:", extra_error)
            driver.save_screenshot("error_extra_submit.png")
        print("質問投稿完了後、1分間待機します。")
        time.sleep(60)
    except Exception as e:
        print("エラー（匿名投稿）:", e)
        driver.save_screenshot("error_anonymous.png")
    finally:
        driver.quit()
    return random_question

# --------------------------------------------
# Part2: 画像ダウンロードと動画生成（requests と FFmpeg 使用）
# --------------------------------------------
def download_image_and_generate_video():
    # Chrome ダウンロード設定（参考用）
    prefs = {
        "download.default_directory": "/Users/yusaku/kakeru/動画", 
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options = Options()
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option("prefs", prefs)
    service2 = Service(ChromeDriverManager().install())
    driver2 = webdriver.Chrome(service=service2, options=chrome_options)
    cookies_file = "mashumaro_cookies.json"
    try:
        login_url = "https://marshmallow-qa.com/session/new"
        driver2.get(login_url)
        wait2 = WebDriverWait(driver2, 20)
        try:
            if os.path.exists(cookies_file):
                with open(cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    if "expiry" in cookie and cookie["expiry"] is None:
                        cookie.pop("expiry")
                    try:
                        driver2.add_cookie(cookie)
                    except Exception as cookie_error:
                        print("クッキー追加エラー:", cookie_error)
                driver2.refresh()
                time.sleep(5)
                print("保存済みのクッキーを読み込みました。")
            else:
                input("ブラウザでログインし、完了後 Enter を押してください。")
                cookies = driver2.get_cookies()
                with open(cookies_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f)
                print("ログイン後のクッキーを保存しました。")
        except Exception as e_cookie:
            print("クッキー関連のエラー:", e_cookie)
            driver2.save_screenshot("cookie_error.png")
        time.sleep(2)
        driver2.get("https://marshmallow-qa.com/messages")
        time.sleep(5)
        wait2 = WebDriverWait(driver2, 20)
        try:
            latest_anchor = wait2.until(EC.presence_of_element_located(
                (By.XPATH, "(//a[contains(@class, 'text-zinc-400') and (contains(text(), '分前') or contains(text(), '秒前'))])[1]")
            ))
            latest_href = latest_anchor.get_attribute("href")
            if latest_href.startswith("http"):
                question_detail_url = latest_href
            else:
                question_detail_url = "https://marshmallow-qa.com" + latest_href
            print("最新の質問 URL:", question_detail_url)
        except Exception as e_latest:
            print("最新の質問リンク取得エラー:", e_latest)
            driver2.save_screenshot("latest_link_error.png")
            raise e_latest
        time.sleep(2)
        driver2.get(question_detail_url)
        time.sleep(5)
        try:
            download_elem = wait2.until(EC.presence_of_element_located(
                (By.XPATH, "//a[.//span[contains(text(), '画像ダウンロード')]]")
            ))
            image_download_url = download_elem.get_attribute("href")
            print("画像ダウンロードURL:", image_download_url)
        except Exception as e_download_elem:
            print("画像ダウンロードリンク取得エラー:", e_download_elem)
            driver2.save_screenshot("download_link_error.png")
            raise e_download_elem
        try:
            response = requests.get(image_download_url)
            if response.status_code == 200:
                save_path = os.path.join("/Users/yusaku/kakeru/動画", "downloaded_image.png")
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print("画像がリクエスト経由で保存されました:", save_path)
            else:
                print("画像ダウンロードに失敗。HTTPステータスコード:", response.status_code)
                raise Exception("HTTPエラー: " + str(response.status_code))
        except Exception as e_requests:
            print("requests で画像ダウンロード中にエラー:", e_requests)
            raise e_requests
    except Exception as e:
        print("エラー（ログイン／画像ダウンロード中）:", e)
        driver2.save_screenshot("error_login_or_download.png")
    finally:
        driver2.quit()
    
    # Part3: 保存された画像から FFmpeg を使用して1分間の動画 (MP4) を生成する
    output_dir = "/Users/yusaku/kakeru/動画"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    downloaded_image = os.path.join(output_dir, "downloaded_image.png")
    # 動画ファイルの出力パス（X投稿用）
    output_video = "/Users/yusaku/kakeru/動画/one_minute_video.mp4"
    
    max_wait = 120
    waited = 0
    while not os.path.exists(downloaded_image) and waited < max_wait:
        time.sleep(1)
        waited += 1
        print(f"画像ファイル未検出。{waited}秒待機中…")
    
    if os.path.exists(downloaded_image):
        print("画像ファイルが検出されました。FFmpeg で動画生成を開始します。")
        # FFmpeg コマンド：入力画像の解像度を偶数に整えるため scale フィルターを追加
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loop", "1",
            "-i", downloaded_image,
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264",
            "-t", "60",
            "-pix_fmt", "yuv420p",
            output_video
        ]
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            print("画像が1分間の動画に変換されました。出力ファイル:", output_video)
        except subprocess.CalledProcessError as cpe:
            print("FFmpeg での動画生成エラー:", cpe)
    else:
        print("エラー: ダウンロードされた画像ファイルが見つかりません。")
        return None
    
    return output_video

# --------------------------------------------
# Part4: X (Twitter/X) に回答と動画を投稿する
# --------------------------------------------
def post_to_x(answer_text, video_path, driver):
    try:
        tweet_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']"))
        )
    except NoSuchElementException:
        print("投稿用テキストエリアが見つかりませんでした。")
        return
    tweet_box.click()
    time.sleep(random_delay(2, 3))
    final_text = f"{answer_text}\n{get_random_emojis(2)}"
    paste_text(driver, tweet_box, final_text)
    time.sleep(random_delay(1, 2))
    
    # 動画ファイルアップロード（絶対パス指定）
    if isinstance(video_path, str) and video_path.strip() != "":
        abs_video_path = os.path.abspath(video_path)
        if os.path.exists(abs_video_path):
            try:
                file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[data-testid='fileInput']")
                if file_inputs:
                    file_input = file_inputs[0]
                    file_input.send_keys(abs_video_path)
                    try:
                        WebDriverWait(driver, 60).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//span[contains(text(), 'アップロード完了（100%）')]")
                            )
                        )
                        print("動画のアップロードが完了しました。")
                    except TimeoutException as te:
                        print("動画アップロード完了待機でタイムアウトしました。", te)
                else:
                    print("動画アップロード用の input[data-testid='fileInput'] が見つかりません。")
            except Exception as e:
                print("動画ファイルの添付失敗:", e)
        else:
            print("動画ファイルが見つかりませんでした:", abs_video_path)
    else:
        print("動画ファイルが存在しません:", video_path)
    
    try:
        post_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tweetButton']"))
        )
        print(" -> tweetButton で投稿ボタンを取得しました。")
    except TimeoutException:
        print("tweetButton が見つからないか、クリック可能になりませんでした。fallbackとして tweetButtonInline を試みます。")
        try:
            post_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='tweetButtonInline']"))
            )
            print(" -> tweetButtonInline で投稿ボタンを取得しました。")
        except TimeoutException:
            print("tweetButtonInline も見つかりませんでした。投稿をスキップします。")
            return
    if post_button:
        try:
            post_button.click()
            print("Xへの投稿が完了しました。")
        except Exception as e:
            print("投稿ボタンのクリックでエラー:", e)
    time.sleep(random_delay(3, 5))

def post_answer_to_x(qanda_jsonl_file, question, x_cookie_file, base_url="https://x.com"):
    driver = create_driver(headless=False)
    if os.path.exists(x_cookie_file):
        with open(x_cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        driver.get(base_url)
        time.sleep(random_delay(2, 4))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"X クッキー追加エラー: {cookie.get('name')} エラー: {e}")
        driver.refresh()
        time.sleep(random_delay(3, 5))
        print("保存済みのXクッキーを読み込みました。")
    else:
        print("Xのクッキーが見つかりません。手動ログインしてください。")
        driver.get(base_url + "/i/flow/login")
        time.sleep(random_delay(3, 6))
        input("ログイン完了後、Enterキーを押してください...")
        cookies = driver.get_cookies()
        with open(x_cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("Xのクッキーを保存しました。")
        driver.get(base_url)
        time.sleep(random_delay(3, 5))
    
    answer_text = find_answer_for_question(qanda_jsonl_file, question)
    if not answer_text:
        print("回答が見つかりませんでした。")
        driver.quit()
        return
    video_path = "/Users/yusaku/kakeru/動画/one_minute_video.mp4"
    if not os.path.exists(video_path):
        print("動画ファイルが存在しません:", video_path)
        driver.quit()
        return
    post_to_x(answer_text, video_path, driver)
    driver.quit()

def find_answer_for_question(jsonl_filepath, question):
    answer = None
    answers = []
    with open(jsonl_filepath, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    prompt = data.get("prompt", "")
                    completion = data.get("completion", "").strip()
                    if question in prompt and completion:
                        answer = completion
                        break
                    if completion:
                        answers.append(completion)
                except Exception as e:
                    print("回答読み込みエラー:", e)
    if not answer and answers:
        answer = random.choice(answers)
    return answer

# --------------------------------------------
# Main 制御
# --------------------------------------------
def main():
    # Part1: マシュマロに匿名で質問投稿し、投稿した質問内容を取得
    question_posted = post_question_anonymously()
    
    # Part2: 画像ダウンロードと動画生成。動画ファイルのフルパスを取得
    video_file_path = download_image_and_generate_video()
    if not video_file_path:
        print("動画生成に失敗しました。")
        return
    
    # Part4: X に対して、JSONLから対応する回答を選び、動画とともに投稿する
    qanda_jsonl_file = "/Users/yusaku/kakeru/qanda.jsonl"  # 質問・回答ペアファイル
    x_cookie_file = "x_cookies.json"  # X 用クッキー保存ファイル
    post_answer_to_x(qanda_jsonl_file, question_posted, x_cookie_file, base_url="https://x.com")

if __name__ == "__main__":
    main()
