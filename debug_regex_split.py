"""
Debug script to understand why regex split isn't working correctly
"""
import re

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

patterns = [
    r'^## ',  # Original pattern
    r'## ',   # Without start of line anchor
    r'\n## ', # With newline
    r'(?:^|\n)## '  # With optional start of line or newline
]

for i, pattern in enumerate(patterns):
    print(f"\nPattern {i+1}: {pattern}")
    sections = re.split(pattern, md_content, flags=re.MULTILINE)
    print(f"Number of sections: {len(sections)}")
    for j, section in enumerate(sections):
        print(f"Section {j}: {section[:50]}...")
