"""
Debug script to understand why QA items are not being parsed correctly
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
    
    if "Q&A" in section_title:
        print("Processing Q&A section")
        qa_items = []
        current_qa = None
        
        for j, line in enumerate(lines[1:]):
            print(f"  Line {j}: {line}")
            
            if line.startswith("- **Q："):
                if current_qa:
                    print(f"    Adding current Q&A: {current_qa['question']}")
                    qa_items.append(current_qa)
                
                q_match = re.match(r'- \*\*Q：(.*?)\*\*', line)
                if q_match:
                    question = q_match.group(1)
                    current_qa = {
                        'type': 'qa',
                        'question': question,
                        'answer': ''
                    }
                    print(f"    Created new Q&A: {question}")
                    
                    a_match = re.search(r'A：(.*?)$', line)
                    if a_match:
                        current_qa['answer'] = a_match.group(1)
                        print(f"    Found answer in same line: {current_qa['answer']}")
            
            elif line.strip().startswith("A：") and current_qa:
                current_qa['answer'] = line.strip().replace("A：", "").strip()
                print(f"    Found answer on separate line: {current_qa['answer']}")
            
            elif line.startswith("- ") and not line.startswith("- **Q："):
                qa_text = line.strip()[2:]  # "- " を削除
                print(f"    Processing non-bold Q&A: {qa_text}")
                
                qa_match = re.match(r'「(.+?)」\s*→\s*(.+?)$', qa_text)
                if qa_match:
                    qa_item = {
                        'type': 'qa',
                        'question': qa_match.group(1),
                        'answer': qa_match.group(2)
                    }
                    qa_items.append(qa_item)
                    print(f"    Added Q&A with arrow format: {qa_item['question']} → {qa_item['answer']}")
                else:
                    qa_item = {
                        'type': 'qa',
                        'question': qa_text,
                        'answer': ''
                    }
                    qa_items.append(qa_item)
                    print(f"    Added Q&A without answer: {qa_item['question']}")
        
        if current_qa:
            print(f"    Adding final Q&A: {current_qa['question']}")
            qa_items.append(current_qa)
        
        print(f"  Total Q&A items in this section: {len(qa_items)}")
        for item in qa_items:
            print(f"    - Q: {item['question']} | A: {item['answer']}")

print("\n=== Running extract_items function ===")
items = extract_items(md_content)
print(f"Total items extracted: {len(items)}")
for item in items:
    if item['type'] == 'job':
        print(f"Job: {item['title']} ({item['date']})")
    elif item['type'] == 'qa':
        print(f"Q&A: {item['question']} | {item['answer']}")
