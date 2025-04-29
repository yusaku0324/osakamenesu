"""
Debug script to understand why extract_items is creating duplicate job items
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

sections = re.split(r'(?=## )', md_content)
print(f"Number of sections: {len(sections)}")

for i, section in enumerate(sections):
    print(f"\n=== Section {i} ===")
    print(f"Section content: {section[:100]}...")
    
    if not section.strip():
        print("Empty section, skipping")
        continue
    
    lines = section.strip().split('\n')
    if not lines:
        print("No lines in section, skipping")
        continue
    
    section_title = lines[0].strip()
    print(f"Section title: {section_title}")
    
    if "メンエス求人情報" in section_title:
        print("Processing job section")
        current_item = None
        job_items = []
        
        for j, line in enumerate(lines[1:]):
            print(f"  Line {j}: {line}")
            
            if line.startswith("- **"):
                if current_item:
                    print(f"    Adding current item: {current_item['title']}")
                    job_items.append(current_item)
                
                title_match = re.match(r'- \*\*(.*?)\*\* - (.*)', line)
                if title_match:
                    current_item = {
                        'type': 'job',
                        'title': title_match.group(1),
                        'date': title_match.group(2),
                        'conditions': [],
                        'video': None
                    }
                    print(f"    Created new item: {current_item['title']}")
            
            elif line.strip().startswith("✅") and current_item:
                current_item['conditions'].append(line.strip())
                print(f"    Added condition to {current_item['title']}")
            
            elif line.strip().startswith("動画:") and current_item:
                current_item['video'] = line.strip().replace("動画:", "").strip()
                print(f"    Added video to {current_item['title']}")
            
            elif not line.strip() and current_item:
                print(f"    Empty line, adding current item: {current_item['title']}")
                job_items.append(current_item)
                current_item = None
        
        if current_item:
            print(f"    Adding final item: {current_item['title']}")
            job_items.append(current_item)
        
        print(f"  Total job items in this section: {len(job_items)}")
        for item in job_items:
            print(f"    - {item['title']} ({item['date']})")

print("\n=== Running extract_items function ===")
items = extract_items(md_content)
print(f"Total items extracted: {len(items)}")
for item in items:
    if item['type'] == 'job':
        print(f"Job: {item['title']} ({item['date']})")
    elif item['type'] == 'qa':
        print(f"Q&A: {item['question']}")
