"""
MarkdownファイルをX投稿用のキューに変換するスクリプト
"""
import json
import re
import datetime
import pathlib
import openai
import os
from dotenv import load_dotenv


load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


def extract_items(md_content):
    """Markdownから投稿アイテムを抽出"""
    job_items = []
    qa_items = []
    
    sections = re.split(r'^## ', md_content, flags=re.MULTILINE)
    
    for section in sections[1:]:  # 最初の空セクションをスキップ
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        section_title = lines[0].strip()
        
        if "メンエス求人情報" in section_title:
            current_item = None
            for line in lines[1:]:
                if line.startswith("- **"):
                    if current_item:
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
                elif line.strip().startswith("✅") and current_item:
                    current_item['conditions'].append(line.strip())
                elif line.strip().startswith("動画:") and current_item:
                    current_item['video'] = line.strip().replace("動画:", "").strip()
            
            if current_item:
                job_items.append(current_item)
        
        elif "Q&A" in section_title:
            current_qa = None
            for line in lines[1:]:
                if line.startswith("- **Q："):
                    if current_qa:
                        qa_items.append(current_qa)
                    
                    q_match = re.match(r'- \*\*Q：(.*?)\*\*', line)
                    if q_match:
                        question = q_match.group(1)
                        current_qa = {
                            'type': 'qa',
                            'question': question,
                            'answer': ''
                        }
                        
                        a_match = re.search(r'A：(.*?)$', line)
                        if a_match:
                            current_qa['answer'] = a_match.group(1)
                elif line.strip().startswith("A：") and current_qa:
                    current_qa['answer'] = line.strip().replace("A：", "").strip()
                elif line.startswith("- ") and not line.startswith("- **Q："):
                    qa_text = line.strip()[2:]  # "- " を削除
                    
                    qa_match = re.match(r'「(.+?)」\s*→\s*(.+?)$', qa_text)
                    if qa_match:
                        qa_items.append({
                            'type': 'qa',
                            'question': qa_match.group(1),
                            'answer': qa_match.group(2)
                        })
                    else:
                        qa_items.append({
                            'type': 'qa',
                            'question': qa_text,
                            'answer': ''
                        })
            
            if current_qa:
                qa_items.append(current_qa)
    
    return job_items + qa_items


def summarize(item):
    """OpenAI APIを使用してアイテムを要約"""
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        
        if item['type'] == 'job':
            content = f"{item['title']} {item['date']}\n"
            content += "\n".join(item['conditions'])
            if item['video']:
                content += f"\n動画: {item['video']}"
            
            prompt = f"""次の求人情報を140字以内のツイートに要約してください。
絵文字を適度に使用し、ハッシュタグを2-3個含めてください。

{content}

ツイート本文のみを出力してください。"""
            
            system_content = "あなたはメンズエステの求人担当者です。"
        
        else:  # Q&A
            content = f"Q：{item['question']}"
            if item['answer']:
                content += f"\nA：{item['answer']}"
            
            prompt = f"""次のQ&Aを140字以内のツイートに要約してください。
絵文字を適度に使用し、ハッシュタグを2-3個含めてください。
質問と回答の要点を簡潔にまとめてください。

{content}

ツイート本文のみを出力してください。"""
            
            system_content = "あなたはメンズエステの業界情報を発信する専門家です。"
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"Error in summarize: {e}")
        
        if item['type'] == 'job':
            conditions = " ".join(item['conditions'][:2]) if 'conditions' in item else ""
            return f"{item['title']} {item['date']} {conditions} #メンエス求人 #出稼ぎ"
        else:  # Q&A
            return f"Q：{item['question']} {item['answer'][:50]}... #メンエスQ&A #よくある質問"


def main():
    today = datetime.date.today().isoformat()
    draft_path = pathlib.Path(f"drafts/{today}.md")
    
    if not draft_path.exists():
        print(f"Draft file not found: {draft_path}")
        return
    
    md_content = draft_path.read_text(encoding='utf-8')
    
    items = extract_items(md_content)
    
    posts = []
    for item in items:
        post_text = summarize(item)
        posts.append({"text": post_text})
    
    queue_dir = pathlib.Path("queue")
    queue_dir.mkdir(exist_ok=True)
    
    queue_path = queue_dir / f"queue_{today}.json"
    queue_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"Queue file created: {queue_path}")
    print(f"Total posts: {len(posts)}")


if __name__ == "__main__":
    main()
