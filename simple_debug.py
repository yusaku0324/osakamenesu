"""
Simple debug script to understand the issue with md2queue.py
"""
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bot.md2queue import extract_items

md_content = """# 2025-04-26 メンエス求人情報＆Q&A


- **新宿エリア** - 2025/04/26
  ✅ 日給3万円以上保証
  ✅ 未経験歓迎
  ✅ 完全個室待機
  動画: https://example.com/video1.mp4

- **渋谷エリア** - 2025/04/26
  ✅ 日給4万円以上可能
  ✅ 経験者優遇
  ✅ 寮完備
  動画: https://example.com/video2.mp4


- **Q：メンエスの出稼ぎは未経験でも大丈夫ですか？** A：はい、未経験の方でも丁寧に研修を行いますので安心してください。
- **Q：出稼ぎの期間はどのくらいですか？** A：最短1週間から可能です。長期の方も歓迎しています。
- 「メンエスの仕事内容は？」 → マッサージとリラクゼーションサービスを提供します。
"""

items = extract_items(md_content)

print(f"Total items extracted: {len(items)}")
for item in items:
    if item['type'] == 'job':
        print(f"Job: {item['title']} ({item['date']})")
    elif item['type'] == 'qa':
        print(f"Q&A: {item['question']} | {item['answer']}")
