"""
Test script to verify the fixed md2queue implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bot.md2queue_fixed import extract_items

md_content_with_sections = """# 2025-04-26 メンエス求人情報＆Q&A


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

md_content_without_sections = """# 2025-04-26 メンエス求人情報＆Q&A

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

print("=== Testing with section headers ===")
items_with_sections = extract_items(md_content_with_sections)
print(f"Total items extracted: {len(items_with_sections)}")

job_items = [item for item in items_with_sections if item['type'] == 'job']
qa_items = [item for item in items_with_sections if item['type'] == 'qa']

print(f"Job items: {len(job_items)}")
for item in job_items:
    print(f"  - {item['title']} ({item['date']})")
    print(f"    Conditions: {len(item['conditions'])}")
    print(f"    Video: {item['video']}")

print(f"Q&A items: {len(qa_items)}")
for item in qa_items:
    print(f"  - Q: {item['question']}")
    print(f"    A: {item['answer']}")

print("\n=== Testing without section headers ===")
items_without_sections = extract_items(md_content_without_sections)
print(f"Total items extracted: {len(items_without_sections)}")

job_items = [item for item in items_without_sections if item['type'] == 'job']
qa_items = [item for item in items_without_sections if item['type'] == 'qa']

print(f"Job items: {len(job_items)}")
for item in job_items:
    print(f"  - {item['title']} ({item['date']})")
    print(f"    Conditions: {len(item['conditions'])}")
    print(f"    Video: {item['video']}")

print(f"Q&A items: {len(qa_items)}")
for item in qa_items:
    print(f"  - Q: {item['question']}")
    print(f"    A: {item['answer']}")
