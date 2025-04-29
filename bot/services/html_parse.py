"""
HTML parsing and Q&A data handling services
"""
import os
import csv
import json
import logging
import re
from typing import Dict, List, Optional, Union, Any
from bot.utils.backoff import with_backoff

logger = logging.getLogger(__name__)

@with_backoff(max_retries=3, initial_delay=1.0)
def load_qa_data(file_path: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    CSVまたはJSONLファイルからQ&Aデータを読み込む
    
    Args:
        file_path: ファイルパス
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）
        
    Returns:
        Dict[str, Any]: Q&Aデータの辞書
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {}
        
        qa_dict = {}
        
        if file_path.endswith('.csv'):
            logger.info(f"Loading Q&A data from CSV: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'question' in row and 'answer' in row:
                        question = row['question'].strip()
                        answer = row['answer'].strip()
                        media_url = row.get('media_url', '').strip()
                        
                        qa_dict[question] = {
                            'text': answer,
                            'media_url': media_url
                        }
            
            logger.info(f"Loaded {len(qa_dict)} Q&A pairs from CSV")
        
        elif file_path.endswith('.jsonl'):
            logger.info(f"Loading Q&A data from JSONL: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    if 'question' in data and 'answer' in data:
                        question = data['question'].strip()
                        answer = data['answer'].strip()
                        media_url = data.get('media_url', '').strip()
                        
                        qa_dict[question] = {
                            'text': answer,
                            'media_url': media_url
                        }
            
            logger.info(f"Loaded {len(qa_dict)} Q&A pairs from JSONL")
        
        else:
            logger.error(f"Unsupported file format: {file_path}")
            return {}
        
        return qa_dict
    
    except Exception as e:
        logger.error(f"Error loading Q&A data: {e}")
        return {}

def find_answer_for_question(qa_dict: Dict[str, Any], question: str, 
                            logger: Optional[logging.Logger] = None) -> Union[Dict[str, str], str]:
    """
    質問に対する回答を検索する
    
    Args:
        qa_dict: Q&Aデータの辞書
        question: 検索する質問
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）
        
    Returns:
        Union[Dict[str, str], str]: 回答データ（辞書または文字列）
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        if question in qa_dict:
            logger.info(f"Found exact match for question: {question}")
            return qa_dict[question]
        
        for q, a in qa_dict.items():
            if q.lower() == question.lower():
                logger.info(f"Found case-insensitive match for question: {question}")
                return a
        
        normalized_question = re.sub(r'[、。？！.,?!]', '', question)
        for q, a in qa_dict.items():
            normalized_q = re.sub(r'[、。？！.,?!]', '', q)
            if normalized_q == normalized_question:
                logger.info(f"Found punctuation-insensitive match for question: {question}")
                return a
        
        best_match = None
        best_match_length = 0
        
        for q, a in qa_dict.items():
            if question in q and len(question) > best_match_length:
                best_match = a
                best_match_length = len(question)
            elif q in question and len(q) > best_match_length:
                best_match = a
                best_match_length = len(q)
        
        if best_match:
            logger.info(f"Found partial match for question: {question}")
            return best_match
        
        def normalize_japanese(text):
            particles = ['の', 'は', 'が', 'を', 'に', 'で', 'と', 'や', 'へ', 'より', 'から', 'まで', 'について']
            normalized = text
            for p in particles:
                normalized = normalized.replace(p, ' ')
            return normalized
        
        normalized_question = normalize_japanese(question)
        question_words = set(w for w in normalized_question.split() if w)
        
        best_match = None
        best_match_count = 0
        best_match_ratio = 0.0
        
        for q, a in qa_dict.items():
            if ('メンエス' in question and 'メンエス' in q and 
                '出稼ぎ' in question and '出稼ぎ' in q):
                logger.info(f"Special case match for 'メンエス' and '出稼ぎ' in '{q}'")
                return a
                
            normalized_q = normalize_japanese(q)
            q_words = set(w for w in normalized_q.split() if w)
            
            common_words = question_words.intersection(q_words)
            
            match_ratio = len(common_words) / max(len(question_words), 1)
            
            if len(common_words) > best_match_count or (len(common_words) == best_match_count and match_ratio > best_match_ratio):
                best_match = a
                best_match_count = len(common_words)
                best_match_ratio = match_ratio
        
        if best_match and best_match_count >= 1:
            logger.info(f"Found word-level match for question: {question} (matched words: {best_match_count}, ratio: {best_match_ratio:.2f})")
            return best_match
        
        logger.warning(f"No match found for question: {question}")
        return {"text": "申し訳ありませんが、この質問に対する回答はまだ用意されていません。", "media_url": ""}
    
    except Exception as e:
        logger.error(f"Error finding answer: {e}")
        return {"text": "回答の検索中にエラーが発生しました。", "media_url": ""}

def load_queue_questions(queue_file: str, logger: Optional[logging.Logger] = None) -> List[Dict[str, str]]:
    """
    キューファイルから質問を読み込む
    
    Args:
        queue_file: キューファイルのパス
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）
        
    Returns:
        List[Dict[str, str]]: 質問のリスト
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        if not os.path.exists(queue_file):
            logger.error(f"Queue file not found: {queue_file}")
            return []
        
        if queue_file.endswith('.yaml') or queue_file.endswith('.yml'):
            import yaml
            with open(queue_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, list):
                logger.error(f"Invalid YAML format in queue file: {queue_file}")
                return []
            
            logger.info(f"Loaded {len(data)} questions from YAML queue")
            return data
        
        elif queue_file.endswith('.json'):
            with open(queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logger.error(f"Invalid JSON format in queue file: {queue_file}")
                return []
            
            logger.info(f"Loaded {len(data)} questions from JSON queue")
            return data
        
        else:
            logger.error(f"Unsupported queue file format: {queue_file}")
            return []
    
    except Exception as e:
        logger.error(f"Error loading queue questions: {e}")
        return []

def update_queue_with_media(queue_file: str, questions: List[Dict[str, str]], 
                           logger: Optional[logging.Logger] = None) -> bool:
    """
    キューファイルをメディアURLで更新する
    
    Args:
        queue_file: キューファイルのパス
        questions: 更新された質問のリスト
        logger: ロガーインスタンス（Noneの場合はモジュールロガーを使用）
        
    Returns:
        bool: 成功したかどうか
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        if queue_file.endswith('.yaml') or queue_file.endswith('.yml'):
            import yaml
            with open(queue_file, 'w', encoding='utf-8') as f:
                yaml.dump(questions, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Updated YAML queue file with media URLs: {queue_file}")
            return True
        
        elif queue_file.endswith('.json'):
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated JSON queue file with media URLs: {queue_file}")
            return True
        
        else:
            logger.error(f"Unsupported queue file format: {queue_file}")
            return False
    
    except Exception as e:
        logger.error(f"Error updating queue with media: {e}")
        return False
