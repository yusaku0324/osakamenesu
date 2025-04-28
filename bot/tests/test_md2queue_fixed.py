"""
Tests for md2queue.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import datetime
import pathlib

from bot.md2queue import (
    extract_items,
    summarize,
    main
)


class TestMd2QueueFunctions(unittest.TestCase):
    """Test markdown to queue conversion functions"""
    
    def setUp(self):
        self.md_content = """# 2025-04-26 メンエス求人情報＆Q&A


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
    
    def test_extract_items_job_info(self):
        """Test extracting job information from markdown"""
        items = extract_items(self.md_content)
        
        job_items = [item for item in items if item['type'] == 'job']
        self.assertEqual(len(job_items), 2)
        
        self.assertEqual(job_items[0]['title'], '新宿エリア')
        self.assertEqual(job_items[0]['date'], '2025/04/26')
        self.assertEqual(len(job_items[0]['conditions']), 3)
        self.assertEqual(job_items[0]['video'], 'https://example.com/video1.mp4')
    
    def test_extract_items_qa(self):
        """Test extracting Q&A from markdown"""
        items = extract_items(self.md_content)
        
        qa_items = [item for item in items if item['type'] == 'qa']
        self.assertEqual(len(qa_items), 3)
        
        self.assertEqual(qa_items[0]['question'], 'メンエスの出稼ぎは未経験でも大丈夫ですか？')
        self.assertEqual(qa_items[0]['answer'], 'はい、未経験の方でも丁寧に研修を行いますので安心してください。')
        
        self.assertEqual(qa_items[2]['question'], 'メンエスの仕事内容は？')
        self.assertEqual(qa_items[2]['answer'], 'マッサージとリラクゼーションサービスを提供します。')
    
    @patch('openai.OpenAI')
    def test_summarize_job_success(self, mock_openai):
        """Test successful job summarization"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "新宿エリア 2025/04/26 日給3万円以上保証 #メンエス求人 #出稼ぎ"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        job_item = {
            'type': 'job',
            'title': '新宿エリア',
            'date': '2025/04/26',
            'conditions': ['✅ 日給3万円以上保証', '✅ 未経験歓迎'],
            'video': 'https://example.com/video1.mp4'
        }
        
        result = summarize(job_item)
        
        self.assertEqual(result, "新宿エリア 2025/04/26 日給3万円以上保証 #メンエス求人 #出稼ぎ")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_summarize_qa_success(self, mock_openai):
        """Test successful Q&A summarization"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Q：メンエスの出稼ぎは未経験でも大丈夫？ A：はい、丁寧な研修があります #メンエスQ&A"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        qa_item = {
            'type': 'qa',
            'question': 'メンエスの出稼ぎは未経験でも大丈夫ですか？',
            'answer': 'はい、未経験の方でも丁寧に研修を行いますので安心してください。'
        }
        
        result = summarize(qa_item)
        
        self.assertEqual(result, "Q：メンエスの出稼ぎは未経験でも大丈夫？ A：はい、丁寧な研修があります #メンエスQ&A")
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_summarize_error(self, mock_openai):
        """Test summarization with error"""
        mock_openai.side_effect = Exception("API error")
        
        job_item = {
            'type': 'job',
            'title': '新宿エリア',
            'date': '2025/04/26',
            'conditions': ['✅ 日給3万円以上保証', '✅ 未経験歓迎'],
            'video': 'https://example.com/video1.mp4'
        }
        
        result = summarize(job_item)
        
        self.assertIn("新宿エリア", result)
        self.assertIn("#メンエス求人", result)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    @patch('pathlib.Path.write_text')
    @patch('pathlib.Path.mkdir')
    @patch('datetime.date')
    @patch('bot.md2queue.extract_items')
    @patch('bot.md2queue.summarize')
    def test_main_success(self, mock_summarize, mock_extract, mock_date, mock_mkdir, mock_write, mock_read, mock_exists):
        """Test successful main function execution"""
        mock_date.today.return_value.isoformat.return_value = "2025-04-26"
        mock_exists.return_value = True
        mock_read.return_value = self.md_content
        mock_extract.return_value = [
            {'type': 'job', 'title': '新宿エリア', 'date': '2025/04/26', 'conditions': [], 'video': None},
            {'type': 'qa', 'question': '質問', 'answer': '回答'}
        ]
        mock_summarize.side_effect = ["求人ツイート", "Q&Aツイート"]
        
        main()
        
        mock_exists.assert_called_once()
        mock_read.assert_called_once()
        mock_extract.assert_called_once()
        self.assertEqual(mock_summarize.call_count, 2)
        mock_mkdir.assert_called_once_with(exist_ok=True)
        mock_write.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('datetime.date')
    def test_main_file_not_found(self, mock_date, mock_exists):
        """Test main function with non-existent file"""
        mock_date.today.return_value.isoformat.return_value = "2025-04-26"
        mock_exists.return_value = False
        
        main()
        
        mock_exists.assert_called_once()


if __name__ == '__main__':
    unittest.main()
