"""
CSVファイルをMarkdown形式に変換するスクリプト
質問回答と案件投稿を分けて処理する
"""
import csv
import os
import sys
import datetime
import re
from pathlib import Path


def parse_csv(csv_path):
    """CSVファイルを解析して投稿データを抽出し、タイプごとに分類"""
    job_posts = []
    qa_posts = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            post = {
                'id': row['id'],
                'content': row['投稿内容'],
                'video_path': row['動画ファイルパス'],
                'char_count': row['文字数'],
                'earnings': row['稼ぎ'],
                'account': row['アカウント'],
                'average': row['アベ'],
                'location': row['場所'],
                'video_title': row['動画タイトル'],
                'video_location': row['動画の場所']
            }
            
            content = post['content'].lower()
            
            is_qa = False
            if '?' in content or '？' in content:
                is_qa = True
            elif any(keyword in content for keyword in ['質問', 'q&a', 'q＆a', 'よくある質問', 'faq']):
                is_qa = True
            elif re.search(r'「.+?」.*?→', content):  # 「質問」→回答 形式
                is_qa = True
            
            if is_qa:
                qa_posts.append(post)
            else:
                job_posts.append(post)
    
    return job_posts, qa_posts


def create_markdown(job_posts, qa_posts, output_dir='drafts'):
    """投稿データをMarkdown形式に変換"""
    today = datetime.date.today().isoformat()
    output_path = Path(output_dir) / f"{today}.md"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {today} ネタ\n\n")
        
        if job_posts:
            locations = {}
            for post in job_posts:
                location = post['location']
                if location not in locations:
                    locations[location] = []
                locations[location].append(post)
            
            for location, location_posts in locations.items():
                f.write(f"## 🔖 {location}メンエス求人情報\n\n")
                
                for post in location_posts:
                    lines = post['content'].split('\n')
                    title = lines[1] if len(lines) > 1 else f"{location}メンエス求人"
                    
                    date_info = ""
                    for line in lines:
                        if "キャンセル枠" in line:
                            date_info = line.split("キャンセル枠")[1].strip()
                            break
                    
                    conditions = []
                    for line in lines:
                        if line.startswith("✅"):
                            conditions.append(line)
                    
                    f.write(f"- **{title}** - キャンセル枠{date_info}\n")
                    for condition in conditions:
                        f.write(f"  {condition}\n")
                    if post['video_path']:
                        f.write(f"  動画: {post['video_title']}\n")
                    f.write("\n")
        
        f.write("## 📝 Q&A 情報\n\n")
        
        if qa_posts:
            for post in qa_posts:
                content = post['content']
                
                questions = []
                
                qa_format = re.findall(r'「(.+?)」\s*→\s*(.+?)(?:\n|$)', content)
                if qa_format:
                    for q, a in qa_format:
                        questions.append(f"- **Q：「{q}」**\n  A：{a}")
                elif re.search(r'Q[：:]\s*(.+?)\s*A[：:]', content, re.IGNORECASE):
                    qa_pairs = re.findall(r'Q[：:]\s*(.+?)\s*A[：:]\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
                    for q, a in qa_pairs:
                        questions.append(f"- **Q：{q.strip()}**\n  A：{a.strip()}")
                elif '?' in content or '？' in content:
                    question_matches = re.findall(r'([^。\n]+[?？])', content)
                    answer_parts = re.split(r'[^。\n]+[?？]', content)
                    
                    for i, q in enumerate(question_matches):
                        if i+1 < len(answer_parts) and answer_parts[i+1].strip():
                            a = answer_parts[i+1].strip()
                            questions.append(f"- **Q：{q.strip()}**\n  A：{a}")
                        else:
                            questions.append(f"- **Q：{q.strip()}**")
                
                if not questions:
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip():
                            questions.append(f"- {line.strip()}")
                
                for question in questions:
                    f.write(f"{question}\n")
                f.write("\n")
        else:
            f.write("- 「個室マッサージって風営法許可いるの？」→ 要まとめ\n")
            f.write("- 「出稼ぎの交通費支給って本当？」→ 要確認\n")
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_markdown.py <csv_file>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    job_posts, qa_posts = parse_csv(csv_path)
    output_path = create_markdown(job_posts, qa_posts)
    
    print(f"Markdown file created: {output_path}")
    print(f"Job posts: {len(job_posts)}")
    print(f"Q&A posts: {len(qa_posts)}")


if __name__ == "__main__":
    main()
