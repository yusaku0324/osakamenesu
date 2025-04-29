"""
Debug script to understand why extract_items isn't finding job and QA items
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

sections = re.split(r'^## ', md_content, flags=re.MULTILINE)
print(f"Number of sections: {len(sections)}")
for i, section in enumerate(sections):
    print(f"\nSection {i}:")
    print(f"First 100 chars: {section[:100]}")
    print(f"Section title: {section.split('\\n')[0] if section else 'No title'}")

items = extract_items(md_content)
print(f"\nExtracted items: {len(items)}")
for item in items:
    print(f"Item type: {item['type']}")
    if item['type'] == 'job':
        print(f"  Title: {item['title']}")
        print(f"  Date: {item['date']}")
    elif item['type'] == 'qa':
        print(f"  Question: {item['question']}")
        print(f"  Answer: {item['answer']}")
