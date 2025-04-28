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
    
    # 求人情報の抽出
    job_pattern = r'- \*\*(.*?)\*\* - (.*?)\n((?:  ✅.*?\n)+)(?:  動画: (.*?)\n)?'
    job_matches = re.finditer(job_pattern, md_content, re.MULTILINE)
    
    for match in job_matches:
        title = match.group(1)
        date = match.group(2)
        conditions_text = match.group(3)
        video = match.group(4)
        
        conditions = [line.strip() for line in conditions_text.split('\n') if line.strip()]
        
        job_items.append({
            'type': 'job',
            'title': title,
            'date': date,
            'conditions': conditions,
            'video': video
        })
    
    # Q&Aの抽出
    qa_pattern1 = r'- \*\*Q：(.*?)\*\* A：(.*?)(?=\n|$)'
    qa_matches1 = re.finditer(qa_pattern1, md_content)
    
    for match in qa_matches1:
        question = match.group(1)
        answer = match.group(2)
        
        qa_items.append({
            'type': 'qa',
            'question': question,
            'answer': answer
        })
    
    qa_pattern2 = r'- 「(.*?)」 → (.*?)(?=\n|$)'
    qa_matches2 = re.finditer(qa_pattern2, md_content)
    
    for match in qa_matches2:
        question = match.group(1)
        answer = match.group(2)
        
        qa_items.append({
            'type': 'qa',
            'question': question,
            'answer': answer
        })
    
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
