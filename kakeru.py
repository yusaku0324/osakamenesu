#!/usr/bin/env python3
import os
import sys
import time
import json
import random
import re
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

def random_delay(min_sec=1, max_sec=3):
    """ランダムな待機時間を返す（秒）"""
    return random.uniform(min_sec, max_sec)

def get_random_emojis(n=2):
    """UTF-8で使える多くの絵文字からランダムにn個選んで連結して返す"""
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
    # ランダムにn個選択して連結して返す
    return ''.join(random.sample(emoji_list, n))

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

def load_cookies(driver, cookie_path, base_url):
    if not os.path.exists(cookie_path):
        print(f"Cookieファイルが見つかりません: {cookie_path}")
        return False
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        print("クッキーを適用します:", cookie_path)
        driver.get(base_url)
        time.sleep(random_delay(2, 4))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
                print(f"  -> Cookie 追加成功: {cookie.get('name')}")
            except Exception as e:
                print(f"  -> Cookie 追加失敗: {cookie.get('name')} エラー: {e}")
                time.sleep(random_delay(0.5, 1.5))
        driver.refresh()
        time.sleep(random_delay(3, 5))
        print(f"クッキーを適用しました: {cookie_path}")
        return True
    except Exception as e:
        print("クッキー読み込み中にエラー:", e)
        return False

def manual_login_flow(driver, cookie_path, base_url):
    print("クッキーがないまたはログイン状態が確認できません。手動ログインしてください。")
    driver.get(base_url + "/i/flow/login")
    time.sleep(random_delay(3, 6))
    input("ログイン完了後、Enterキーを押してください...")
    cookies = driver.get_cookies()
    try:
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("クッキーを保存しました。")
    except Exception as e:
        print("クッキー保存中にエラー:", e)
    driver.get(base_url)
    time.sleep(random_delay(3, 6))

def is_logged_in(driver):
    try:
        driver.find_element(By.CSS_SELECTOR, "a[data-testid='SideNav_NewTweet_Button']")
        return True
    except Exception:
        return False

def load_posts(csv_file):
    df = pd.read_csv(csv_file, encoding='utf-8')
    return df

def click_element(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(random_delay(1, 2))
        element.click()
    except ElementClickInterceptedException:
        print("通常クリックが要素被りで失敗したため、JSクリックを試します。")
        driver.execute_script("arguments[0].click();", element)

def paste_text(driver, element, text):
    pyperclip.copy(text)
    if sys.platform.startswith('darwin'):
        paste_keys = (Keys.COMMAND, 'v')
    else:
        paste_keys = (Keys.CONTROL, 'v')
    element.send_keys(*paste_keys)

def post_tweet(post_text, video_path, driver):
    try:
        tweet_box = driver.find_element(By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0']")
    except NoSuchElementException:
        print("投稿用テキストエリアが見つかりませんでした。")
        return
    tweet_box.click()
    time.sleep(random_delay(2, 3))
    
    # 改行してランダムな絵文字2つを追加
    final_text = f"{post_text}\n{get_random_emojis(2)}"
    paste_text(driver, tweet_box, final_text)
    time.sleep(random_delay(1, 2))
    
    # 動画ファイルアップロード
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
                        print("動画のアップロード完了待機でタイムアウトしました。", te)
                else:
                    print("  -> 動画アップロード用の input[data-testid='fileInput'] が見つかりません。")
            except Exception as e:
                print(f"  -> 動画ファイルの添付失敗: {e}")
        else:
            print(f"  -> 動画ファイルが見つかりませんでした: {abs_video_path}")
    
    # 投稿ボタン取得とクリック
    post_button = None
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
            click_element(driver, post_button)
        except Exception as e:
            print("投稿ボタンをクリックできませんでした:", e)
    time.sleep(random_delay(3, 5))

def run_for_account(cookie_file, csv_file, base_url, pick_count, default_video_path):
    driver = create_driver(headless=False)
    
    if not load_cookies(driver, cookie_file, base_url):
        manual_login_flow(driver, cookie_file, base_url)
    else:
        driver.get(base_url)
        time.sleep(random_delay(3, 5))
    
    if not is_logged_in(driver):
        manual_login_flow(driver, cookie_file, base_url)
    
    try:
        posts_df = load_posts(csv_file)
        actual_pick = min(pick_count, len(posts_df))
        sample_posts = posts_df.sample(n=actual_pick)
        for idx, row in sample_posts.iterrows():
            post_text = row["投稿内容"]
            video_path = row.get("動画ファイルパス", "").strip()
            if not video_path:
                video_path = default_video_path
            print(f"投稿する内容: {post_text[:30]}... | 動画: {video_path}")
            post_tweet(post_text, video_path, driver)
            time.sleep(random_delay(10, 20))
    finally:
        driver.quit()

def main():
    # accounts.json の絶対パスを指定
    config_file = "/Users/yusaku/kakeru/accounts.json"
    if not os.path.exists(config_file):
        print(f"{config_file} が見つかりません。終了します。")
        sys.exit(1)
    
    with open(config_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    accounts = data.get("accounts", [])
    if not accounts:
        print("accounts が定義されていません。終了します。")
        sys.exit(1)
    
    for account_info in accounts:
        cookie_file = account_info.get("cookie_file")
        csv_file = account_info.get("csv_file")
        base_url = account_info.get("base_url", "https://x.com")
        pick_count = account_info.get("pick_count", 1)
        default_video_path = account_info.get("video_file_path", "").strip()
        
        if not cookie_file or not csv_file:
            print("cookie_file または csv_file が設定されていません。スキップします。")
            continue
        
        print(f"\n--- アカウント処理開始: cookie_file={cookie_file}, csv_file={csv_file}, pick_count={pick_count} ---")
        run_for_account(cookie_file, csv_file, base_url, pick_count, default_video_path)
        print(f"--- アカウント処理完了: {cookie_file} ---\n")

if __name__ == "__main__":
    while True:
        main()
        # 10～11分（600～660秒）待機する
        wait_seconds = random.randint(600, 660)
        print(f"次の実行まで {wait_seconds} 秒待機します...")
        time.sleep(wait_seconds)
