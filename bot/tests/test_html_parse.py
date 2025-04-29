"""
Tests for html_parse.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import csv

from bot.services.html_parse import (
    load_qa_data,
    find_answer_for_question,
    load_queue_questions,
    update_queue_with_media
)


class TestHtmlParseFunctions(unittest.TestCase):
    """Test HTML parsing and Q&A data handling functions"""
    
    def setUp(self):
        self.csv_data = """question,answer,media_url
質問1,回答1,https://example.com/media1.png
質問2,回答2,https://example.com/media2.png
"""
        self.jsonl_data = """{"question": "質問1", "answer": "回答1", "media_url": "https://example.com/media1.png"}
{"question": "質問2", "answer": "回答2", "media_url": "https://example.com/media2.png"}
"""
        self.yaml_data = """- text: 質問1
  png_url: https://example.com/image1.png
- text: 質問2
  png_url: https://example.com/image2.png
"""
        self.json_data = """[
    {"text": "質問1", "png_url": "https://example.com/image1.png"},
    {"text": "質問2", "png_url": "https://example.com/image2.png"}
]"""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('csv.DictReader')
    def test_load_qa_data_csv_success(self, mock_csv_reader, mock_file, mock_exists):
        """Test successful CSV Q&A data loading"""
        mock_exists.return_value = True
        mock_csv_reader.return_value = [
            {'question': '質問1', 'answer': '回答1', 'media_url': 'https://example.com/media1.png'},
            {'question': '質問2', 'answer': '回答2', 'media_url': 'https://example.com/media2.png'}
        ]
        
        result = load_qa_data("test.csv")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result['質問1']['text'], '回答1')
        self.assertEqual(result['質問1']['media_url'], 'https://example.com/media1.png')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.loads')
    def test_load_qa_data_jsonl_success(self, mock_json_loads, mock_file, mock_exists):
        """Test successful JSONL Q&A data loading"""
        mock_exists.return_value = True
        mock_file.return_value.__enter__.return_value = self.jsonl_data.strip().split('\n')
        mock_json_loads.side_effect = [
            {'question': '質問1', 'answer': '回答1', 'media_url': 'https://example.com/media1.png'},
            {'question': '質問2', 'answer': '回答2', 'media_url': 'https://example.com/media2.png'}
        ]
        
        result = load_qa_data("test.jsonl")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result['質問1']['text'], '回答1')
        self.assertEqual(result['質問1']['media_url'], 'https://example.com/media1.png')
    
    @patch('os.path.exists')
    def test_load_qa_data_file_not_found(self, mock_exists):
        """Test Q&A data loading with non-existent file"""
        mock_exists.return_value = False
        
        result = load_qa_data("nonexistent.csv")
        
        self.assertEqual(result, {})
    
    @patch('os.path.exists')
    def test_load_qa_data_unsupported_format(self, mock_exists):
        """Test Q&A data loading with unsupported format"""
        mock_exists.return_value = True
        
        result = load_qa_data("test.txt")
        
        self.assertEqual(result, {})
    
    def test_find_answer_for_question_exact_match(self):
        """Test finding answer with exact match"""
        qa_dict = {
            '質問1': {'text': '回答1', 'media_url': 'https://example.com/media1.png'},
            '質問2': {'text': '回答2', 'media_url': 'https://example.com/media2.png'}
        }
        
        result = find_answer_for_question(qa_dict, '質問1')
        
        self.assertEqual(result['text'], '回答1')
        self.assertEqual(result['media_url'], 'https://example.com/media1.png')
    
    def test_find_answer_for_question_case_insensitive(self):
        """Test finding answer with case-insensitive match"""
        qa_dict = {
            'Question1': {'text': 'Answer1', 'media_url': 'https://example.com/media1.png'}
        }
        
        result = find_answer_for_question(qa_dict, 'question1')
        
        self.assertEqual(result['text'], 'Answer1')
    
    def test_find_answer_for_question_punctuation_insensitive(self):
        """Test finding answer with punctuation-insensitive match"""
        qa_dict = {
            '質問1？': {'text': '回答1', 'media_url': 'https://example.com/media1.png'}
        }
        
        result = find_answer_for_question(qa_dict, '質問1')
        
        self.assertEqual(result['text'], '回答1')
    
    def test_find_answer_for_question_partial_match(self):
        """Test finding answer with partial match"""
        qa_dict = {
            'これは長い質問です': {'text': '回答', 'media_url': 'https://example.com/media.png'}
        }
        
        result = find_answer_for_question(qa_dict, '長い質問')
        
        self.assertEqual(result['text'], '回答')
    
    def test_find_answer_for_question_word_match(self):
        """Test finding answer with word-level match"""
        qa_dict = {
            'メンエスの出稼ぎについて': {'text': '回答', 'media_url': 'https://example.com/media.png'}
        }
        
        result = find_answer_for_question(qa_dict, 'メンエス 出稼ぎ')
        
        self.assertEqual(result['text'], '回答')
    
    def test_find_answer_for_question_no_match(self):
        """Test finding answer with no match"""
        qa_dict = {
            '質問1': {'text': '回答1', 'media_url': 'https://example.com/media1.png'}
        }
        
        result = find_answer_for_question(qa_dict, '全く違う質問')
        
        self.assertEqual(result['text'], '申し訳ありませんが、この質問に対する回答はまだ用意されていません。')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_load_queue_questions_yaml_success(self, mock_yaml_load, mock_file, mock_exists):
        """Test successful YAML queue loading"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = [
            {'text': '質問1', 'png_url': 'https://example.com/image1.png'},
            {'text': '質問2', 'png_url': 'https://example.com/image2.png'}
        ]
        
        result = load_queue_questions("queue.yaml")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['text'], '質問1')
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_queue_questions_json_success(self, mock_json_load, mock_file, mock_exists):
        """Test successful JSON queue loading"""
        mock_exists.return_value = True
        mock_json_load.return_value = [
            {'text': '質問1', 'png_url': 'https://example.com/image1.png'},
            {'text': '質問2', 'png_url': 'https://example.com/image2.png'}
        ]
        
        result = load_queue_questions("queue.json")
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['text'], '質問1')
    
    @patch('os.path.exists')
    def test_load_queue_questions_file_not_found(self, mock_exists):
        """Test queue loading with non-existent file"""
        mock_exists.return_value = False
        
        result = load_queue_questions("nonexistent.yaml")
        
        self.assertEqual(result, [])
    
    @patch('os.path.exists')
    def test_load_queue_questions_unsupported_format(self, mock_exists):
        """Test queue loading with unsupported format"""
        mock_exists.return_value = True
        
        result = load_queue_questions("queue.txt")
        
        self.assertEqual(result, [])
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_update_queue_with_media_yaml_success(self, mock_yaml_dump, mock_file):
        """Test successful YAML queue update"""
        questions = [
            {'text': '質問1', 'png_url': 'https://example.com/image1.png'},
            {'text': '質問2', 'png_url': 'https://example.com/image2.png'}
        ]
        
        result = update_queue_with_media("queue.yaml", questions)
        
        self.assertTrue(result)
        mock_yaml_dump.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_update_queue_with_media_json_success(self, mock_json_dump, mock_file):
        """Test successful JSON queue update"""
        questions = [
            {'text': '質問1', 'png_url': 'https://example.com/image1.png'},
            {'text': '質問2', 'png_url': 'https://example.com/image2.png'}
        ]
        
        result = update_queue_with_media("queue.json", questions)
        
        self.assertTrue(result)
        mock_json_dump.assert_called_once()
    
    def test_update_queue_with_media_unsupported_format(self):
        """Test queue update with unsupported format"""
        questions = [{'text': '質問1', 'png_url': 'https://example.com/image1.png'}]
        
        result = update_queue_with_media("queue.txt", questions)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
