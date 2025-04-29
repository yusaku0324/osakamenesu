"""
Tests for schedule.py
"""
import unittest
from unittest.mock import patch, MagicMock, call
import os
import datetime
import schedule

from bot.schedule import (
    run_scheduled_job,
    schedule_daily_posting,
    schedule_multiple_accounts,
    run_scheduler
)


class TestScheduleFunctions(unittest.TestCase):
    """Test scheduling functions"""
    
    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_job_func = MagicMock()
        self.mock_job_func.__name__ = "mock_job_func"
    
    @patch('bot.schedule.logger')
    def test_run_scheduled_job_success(self, mock_logger):
        """Test successful scheduled job execution"""
        run_scheduled_job(self.mock_job_func, "arg1", kwarg1="value1")
        
        self.mock_job_func.assert_called_once_with("arg1", kwarg1="value1")
        mock_logger.info.assert_has_calls([
            call(f"Running scheduled job: {self.mock_job_func.__name__}"),
            call(f"Scheduled job completed: {self.mock_job_func.__name__}")
        ])
    
    @patch('bot.schedule.logger')
    def test_run_scheduled_job_failure(self, mock_logger):
        """Test scheduled job execution with error"""
        self.mock_job_func.side_effect = Exception("Test error")
        
        run_scheduled_job(self.mock_job_func)
        
        self.mock_job_func.assert_called_once()
        mock_logger.error.assert_called()
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.getenv')
    def test_schedule_daily_posting_default(self, mock_getenv, mock_schedule, mock_logger):
        """Test scheduling daily posting with default parameters"""
        mock_getenv.return_value = "default_qa.csv"
        mock_every = MagicMock()
        mock_schedule.every.return_value = mock_every
        mock_day = MagicMock()
        mock_every.day = mock_day
        mock_at = MagicMock()
        mock_day.at.return_value = mock_at
        
        schedule_daily_posting()
        
        mock_getenv.assert_called_once_with("JSONL_PATH", "qa_sheet_polite_fixed.csv")
        mock_day.at.assert_called_once_with("09:00")
        mock_at.do.assert_called_once()
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    def test_schedule_daily_posting_custom(self, mock_schedule, mock_logger):
        """Test scheduling daily posting with custom parameters"""
        mock_every = MagicMock()
        mock_schedule.every.return_value = mock_every
        mock_day = MagicMock()
        mock_every.day = mock_day
        mock_at = MagicMock()
        mock_day.at.return_value = mock_at
        
        schedule_daily_posting(time_str="10:30", queue_file="custom_queue.yaml", qa_file="custom_qa.csv")
        
        mock_day.at.assert_called_once_with("10:30")
        mock_at.do.assert_called_once()
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('yaml.safe_load')
    def test_schedule_multiple_accounts_success(self, mock_yaml_load, mock_open, mock_exists, mock_schedule, mock_logger):
        """Test scheduling multiple accounts successfully"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = [
            {'name': 'account1', 'cookie_path': '/path/to/cookie1.json'},
            {'name': 'account2', 'cookie_path': '/path/to/cookie2.json'}
        ]
        mock_every = MagicMock()
        mock_schedule.every.return_value = mock_every
        mock_day = MagicMock()
        mock_every.day = mock_day
        mock_at = MagicMock()
        mock_day.at.return_value = mock_at
        
        schedule_multiple_accounts("accounts.yaml")
        
        mock_exists.assert_any_call("accounts.yaml")
        mock_yaml_load.assert_called_once()
        self.assertEqual(mock_day.at.call_count, 20)  # 2 accounts * 10 posts per day
    
    @patch('bot.schedule.logger')
    @patch('os.path.exists')
    def test_schedule_multiple_accounts_file_not_found(self, mock_exists, mock_logger):
        """Test scheduling multiple accounts with non-existent file"""
        mock_exists.return_value = False
        
        schedule_multiple_accounts("nonexistent.yaml")
        
        mock_logger.error.assert_called_once_with("Accounts file not found: nonexistent.yaml")
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('yaml.safe_load')
    def test_schedule_multiple_accounts_invalid_format(self, mock_yaml_load, mock_open, mock_exists, mock_schedule, mock_logger):
        """Test scheduling multiple accounts with invalid format"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = "not a list"
        
        schedule_multiple_accounts("accounts.yaml")
        
        mock_logger.error.assert_called_once_with("Invalid accounts format in accounts.yaml")
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('yaml.safe_load')
    @patch('time.sleep')
    @patch('bot.schedule.schedule_daily_posting')
    @patch('bot.schedule.schedule_multiple_accounts')
    def test_run_scheduler_with_config(self, mock_schedule_multiple, mock_schedule_daily, mock_sleep, mock_yaml_load, mock_open, mock_exists, mock_schedule, mock_logger):
        """Test running scheduler with config file"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {
            'daily_posting': {
                'time': '10:00',
                'queue_file': 'daily_queue.yaml',
                'qa_file': 'daily_qa.csv'
            },
            'multiple_accounts': {
                'accounts_file': 'accounts.yaml',
                'start_time': '09:00',
                'posts_per_day': 5,
                'qa_file': 'multi_qa.csv'
            }
        }
        mock_schedule.run_pending.side_effect = KeyboardInterrupt()
        
        result = run_scheduler()
        
        self.assertEqual(result, 0)
        mock_exists.assert_any_call('scheduler_config.yaml')
        mock_yaml_load.assert_called_once()
        mock_schedule_daily.assert_called_once_with(
            time_str='10:00',
            queue_file='daily_queue.yaml',
            qa_file='daily_qa.csv'
        )
        mock_schedule_multiple.assert_called_once_with(
            accounts_file='accounts.yaml',
            time_str='09:00',
            posts_per_day=5,
            qa_file='multi_qa.csv'
        )
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.path.exists')
    @patch('time.sleep')
    def test_run_scheduler_without_config(self, mock_sleep, mock_exists, mock_schedule, mock_logger):
        """Test running scheduler without config file"""
        mock_exists.return_value = False
        mock_schedule.run_pending.side_effect = KeyboardInterrupt()
        
        result = run_scheduler()
        
        self.assertEqual(result, 0)
        mock_exists.assert_any_call('scheduler_config.yaml')
    
    @patch('bot.schedule.logger')
    @patch('bot.schedule.schedule')
    @patch('os.path.exists')
    @patch('time.sleep')
    def test_run_scheduler_error(self, mock_sleep, mock_exists, mock_schedule, mock_logger):
        """Test running scheduler with error"""
        mock_exists.side_effect = Exception("Test error")
        
        result = run_scheduler()
        
        self.assertEqual(result, 1)
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main()
