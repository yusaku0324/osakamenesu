"""
Tests for main.py
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

from bot.main import main, parse_args


class TestMainFunctions(unittest.TestCase):
    """Test main module functions"""
    
    def setUp(self):
        self.test_queue_file = "test_queue.yaml"
        self.test_account = "test_account"
    
    @patch('bot.main.argparse.ArgumentParser.parse_args')
    def test_parse_args_default(self, mock_parse_args):
        """Test parse_args with default values"""
        mock_parse_args.return_value = MagicMock(
            queue_file=None,
            account=None,
            dry_run=False,
            verbose=False
        )
        
        args = parse_args()
        
        self.assertIsNone(args.queue_file)
        self.assertIsNone(args.account)
        self.assertFalse(args.dry_run)
        self.assertFalse(args.verbose)
    
    @patch('bot.main.argparse.ArgumentParser.parse_args')
    def test_parse_args_with_values(self, mock_parse_args):
        """Test parse_args with custom values"""
        mock_parse_args.return_value = MagicMock(
            queue_file=self.test_queue_file,
            account=self.test_account,
            dry_run=True,
            verbose=True
        )
        
        args = parse_args()
        
        self.assertEqual(args.queue_file, self.test_queue_file)
        self.assertEqual(args.account, self.test_account)
        self.assertTrue(args.dry_run)
        self.assertTrue(args.verbose)
    
    @patch('bot.main.setup_logging')
    @patch('bot.main.load_dotenv')
    @patch('bot.main.parse_args')
    @patch('bot.main.run_scheduler')
    def test_main_scheduler_mode(self, mock_run_scheduler, mock_parse_args, mock_load_dotenv, mock_setup_logging):
        """Test main function in scheduler mode"""
        mock_parse_args.return_value = MagicMock(
            queue_file=None,
            account=None,
            dry_run=False,
            verbose=False
        )
        
        result = main()
        
        self.assertEqual(result, 0)
        mock_setup_logging.assert_called_once()
        mock_load_dotenv.assert_called_once()
        mock_run_scheduler.assert_called_once()
    
    @patch('bot.main.setup_logging')
    @patch('bot.main.load_dotenv')
    @patch('bot.main.parse_args')
    @patch('bot.main.post_to_twitter')
    @patch('bot.main.yaml.safe_load')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_main_single_post_mode(self, mock_open, mock_yaml_load, mock_post_to_twitter, mock_parse_args, mock_load_dotenv, mock_setup_logging):
        """Test main function in single post mode"""
        mock_parse_args.return_value = MagicMock(
            queue_file=self.test_queue_file,
            account=self.test_account,
            dry_run=False,
            verbose=False
        )
        mock_yaml_load.return_value = {
            'posts': [
                {'text': 'Test post 1'},
                {'text': 'Test post 2'}
            ]
        }
        mock_post_to_twitter.return_value = {'success': True}
        
        result = main()
        
        self.assertEqual(result, 0)
        mock_setup_logging.assert_called_once()
        mock_load_dotenv.assert_called_once()
        mock_open.assert_called_once_with(self.test_queue_file, 'r', encoding='utf-8')
        mock_yaml_load.assert_called_once()
        self.assertEqual(mock_post_to_twitter.call_count, 2)
    
    @patch('bot.main.setup_logging')
    @patch('bot.main.load_dotenv')
    @patch('bot.main.parse_args')
    @patch('bot.main.post_to_twitter')
    @patch('bot.main.yaml.safe_load')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_main_dry_run(self, mock_open, mock_yaml_load, mock_post_to_twitter, mock_parse_args, mock_load_dotenv, mock_setup_logging):
        """Test main function in dry run mode"""
        mock_parse_args.return_value = MagicMock(
            queue_file=self.test_queue_file,
            account=self.test_account,
            dry_run=True,
            verbose=False
        )
        mock_yaml_load.return_value = {
            'posts': [
                {'text': 'Test post 1'}
            ]
        }
        
        result = main()
        
        self.assertEqual(result, 0)
        mock_setup_logging.assert_called_once()
        mock_load_dotenv.assert_called_once()
        mock_open.assert_called_once_with(self.test_queue_file, 'r', encoding='utf-8')
        mock_yaml_load.assert_called_once()
        mock_post_to_twitter.assert_not_called()
    
    @patch('bot.main.setup_logging')
    @patch('bot.main.load_dotenv')
    @patch('bot.main.parse_args')
    @patch('bot.main.logger')
    def test_main_file_not_found(self, mock_logger, mock_parse_args, mock_load_dotenv, mock_setup_logging):
        """Test main function with file not found error"""
        mock_parse_args.return_value = MagicMock(
            queue_file="nonexistent.yaml",
            account=self.test_account,
            dry_run=False,
            verbose=False
        )
        
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = main()
        
        self.assertEqual(result, 1)
        mock_logger.error.assert_called_once()
    
    @patch('bot.main.setup_logging')
    @patch('bot.main.load_dotenv')
    @patch('bot.main.parse_args')
    @patch('bot.main.logger')
    def test_main_exception(self, mock_logger, mock_parse_args, mock_load_dotenv, mock_setup_logging):
        """Test main function with unexpected exception"""
        mock_parse_args.return_value = MagicMock(
            queue_file=self.test_queue_file,
            account=self.test_account,
            dry_run=False,
            verbose=False
        )
        
        with patch('builtins.open', side_effect=Exception("Unexpected error")):
            result = main()
        
        self.assertEqual(result, 1)
        mock_logger.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
