#!/usr/bin/env python3
"""auto_marshmallow_xbot.py  ✅ 完全版  v2025‑04‑21e
────────────────────────────────────────────────────────
◆ 機能概要
    1.  匿名質問を Marshmallow へ投稿（2 段「おくる / 確認」に対応）
    2.  投稿完了後、最新メッセージ本文 + 画像を取得（猫ページ検知・3 回リトライ）
    3.  画像を FFmpeg で 60 秒ループ動画へ変換
    4.  Q&A CSV / JSONL から回答抽出 → 動画付きで X に投稿
    5.  `login / once / loop --min --max` CLI。loop は可変間隔で実行

◆ 変更履歴
    • v2025‑04‑21e  … 優先表示モーダル自動閉処理を追加、コード整形
"""
from __future__ import annotations

import argparse, csv, json, logging, os, random, subprocess, sys, time, yaml, schedule, requests
from pathlib import Path
from typing import List
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# ──────────────────── 環境 & ログ ────────────────────
load_dotenv()
ROOT            = Path(__file__).resolve().parent
ENV_VIDEO_DIR   = Path(os.getenv("VIDEO_DIR", ROOT / "videos")); ENV_VIDEO_DIR.mkdir(exist_ok=True)
ENV_QA_PATH     = Path(os.getenv("JSONL_PATH", ROOT / "qa_sheet_polite_fixed.csv"))
ENV_MASH_URL    = os.getenv("MARSHMALLOW_URL", "https://marshmallow-qa.com/a3qdqlchqhk06ug?t=Co4zKo")
CONFIG_YAML     = ROOT / "accounts.yaml"
BASE_PROFILEDIR = ROOT / "profiles"; BASE_PROFILEDIR.mkdir(exist_ok=True)
BASE_COOKIEDIR  = ROOT / "cookies" ; BASE_COOKIEDIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s | %(message)s",
    handlers=[logging.FileHandler("bot.log", "a", "utf-8"), logging.StreamHandler(sys.stdout)],
)
L = logging.getLogger("bot")

# ──────────────────── Utils ────────────────────

def rdelay(a: float = 1.0, b: float = 3.0):
    time.sleep(random.uniform(a, b))

def emojis(n: int = 2) -> str:
    pool = "😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱"
    return "".join(random.sample(pool, n))

def cfg_yaml() -> dict:
    return yaml.safe_load(CONFIG_YAML.read_text())

# ──────────────────── Driver Factory ────────────────────

def make_driver(acc: str):
    cfg = cfg_yaml()["accounts"].get(acc)
    if not cfg:
        raise KeyError(f"{acc} not found in accounts.yaml")

    opt = Options()
    opt.add_argument(f"--user-agent={cfg['user_agent']}")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    profile = Path(cfg.get("profile") or BASE_PROFILEDIR / acc)
    opt.add_argument(f"--user-data-dir={profile}")
    if cfg.get("proxy"):
        opt.add_argument(f"--proxy-server={cfg['proxy']}")

    drv = uc.Chrome(options=opt, headless=False, version_main=135)
    drv.implicitly_wait(10)

    cookie_file = BASE_COOKIEDIR / f"{acc}.json"
    if cookie_file.exists():
        drv.get("https://x.com")
        for c in json.load(cookie_file.open()):
            if c.get("expiry") is None:
                c.pop("expiry", None)
            try:
                drv.add_cookie(c)
            except Exception:
                pass
        drv.refresh()
    return drv, cookie_file

def save_cookies(drv, path: Path):
    path.write_text(json.dumps(drv.get_cookies(), ensure_ascii=False, indent=2))

# ──────────────────── Q&A 読み込み ────────────────────

def questions() -> List[str]:
    if ENV_QA_PATH.suffix == ".csv":
        with ENV_QA_PATH.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row["prompt"].split("->")[0].strip() for row in reader if row.get("prompt")]
    else:
        return [json.loads(l)["prompt"].split("->")[0].strip() for l in ENV_QA_PATH.read_text().splitlines() if l.strip()]

# ──────────────────── Marshmallow 投稿 ────────────────────

def is_cat(drv):
    return "エラーが発生しました" in drv.page_source and "猫" in drv.page_source


def safeclick(drv, elem, retry=5, wait=0.6):
    for _ in range(retry):
        try:
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
            drv.execute_script("arguments[0].click();", elem)
            return True
        except Exception:
            time.sleep(wait)
    return False


def close_priority_modal(drv):
    try:
        modal = drv.find_element(By.CSS_SELECTOR, 'div[data-message-form-target="priorityExplanationModal"].modal')
        if modal.is_displayed():
            close_btn = modal.find_element(By.CSS_SELECTOR, '[data-bs-dismiss="modal"]')
            drv.execute_script("arguments[0].click()", close_btn)
            time.sleep(0.5)
    except NoSuchElementException:
        pass


def post_question(drv):
    drv.get(ENV_MASH_URL)
    if is_cat(drv):
        raise RuntimeError("cat page")

    q = random.choice(questions())
    area = WebDriverWait(drv, 20).until(EC.element_to_be_clickable((By.ID, "message_content")))
    area.clear(); area.send_keys(q)

    # 1st おくる
    btn1 = WebDriverWait(drv, 20).until(EC.element_to_be_clickable((By.XPATH,
        "//*[(@role='button' or name()='button') and contains(normalize-space(.), 'おくる')]")))
    safeclick(drv, btn1)
    L.info("1st おくる: %s", q)

    close_priority_modal(drv)  # 優先表示モーダルを閉じる

    # 2nd ボタン
    try:
        btn2 = WebDriverWait(drv, 8).until(EC.element_to_be_clickable((By.CSS_SELECTOR,
            "form#new_message button[type='submit'].btn-primary")))
        safeclick(drv, btn2)
        L.info("2nd おくるクリック成功")
    except TimeoutException:
        L.warning("2nd おくる未表示 – スキップ")

    rdelay(2, 4)
    return q

# ──────────────────── 最新メッセージ＆画像 ────────────────────

def latest_image(drv, retry=3):
    drv.get("https://marshmallow-qa.com/messages")
    for _ in range(retry):
        link = WebDriverWait(drv, 20).until(EC.element_to_be_clickable((By.XPATH,
            "(//a[contains(@href,'/messages/') and .//time])[1]")))
        drv.get(link.get_attribute("href"))
        if is_cat(drv):
            L.warning("cat page – retry"); rdelay(10, 15); drv.back(); continue
        try:
            body = drv.find_element(By.CSS_SELECTOR, "div.whitespace-pre-line").text.strip()
            if body:
                dl = drv.find_element(By.XPATH, "//a[.//span[contains(text(),'画像ダウンロード')]]")
                img_url = dl.get_attribute("href")
                img_path = ENV_VIDEO_DIR / "marshmallow.png"
                img_path.write_bytes(requests.get(img_url, timeout=10).content)
                L.info("画像DL: %s", img_path)
                return img_path
        except Exception:
            pass
        rdelay