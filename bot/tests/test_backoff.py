"""
Tests for backoff.py
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time
import random

from bot.utils.backoff import with_backoff, calculate_backoff_delay


class TestBackoffFunctions(unittest.TestCase):
    """Test backoff utility functions"""
    
    def setUp(self):
        self.mock_func = MagicMock()
        self.mock_func.__name__ = "mock_func"
    
    def test_calculate_backoff_delay_no_jitter(self):
        """Test backoff delay calculation without jitter"""
        delay = calculate_backoff_delay(0, initial_delay=1.0, jitter=False)
        self.assertEqual(delay, 1.0)
        
        delay = calculate_backoff_delay(1, initial_delay=1.0, jitter=False)
        self.assertEqual(delay, 2.0)
        
        delay = calculate_backoff_delay(2, initial_delay=1.0, jitter=False)
        self.assertEqual(delay, 4.0)
    
    @patch('random.random')
    def test_calculate_backoff_delay_with_jitter(self, mock_random):
        """Test backoff delay calculation with jitter"""
        mock_random.return_value = 0.5  # 0.5 + 0.5 = 1.0 multiplier
        
        delay = calculate_backoff_delay(0, initial_delay=1.0, jitter=True)
        self.assertEqual(delay, 1.0)
        
        delay = calculate_backoff_delay(1, initial_delay=1.0, jitter=True)
        self.assertEqual(delay, 2.0)
    
    def test_calculate_backoff_delay_max_delay(self):
        """Test backoff delay calculation with max delay"""
        delay = calculate_backoff_delay(10, initial_delay=1.0, max_delay=10.0, jitter=False)
        self.assertEqual(delay, 10.0)
    
    @patch('time.sleep')
    def test_with_backoff_success_first_try(self, mock_sleep):
        """Test with_backoff decorator with success on first try"""
        self.mock_func.return_value = "success"
        
        decorated_func = with_backoff()(self.mock_func)
        
        result = decorated_func("arg1", kwarg1="value1")
        
        self.mock_func.assert_called_once_with("arg1", kwarg1="value1")
        
        mock_sleep.assert_not_called()
        
        self.assertEqual(result, "success")
    
    @patch('time.sleep')
    def test_with_backoff_retry_then_success(self, mock_sleep):
        """Test with_backoff decorator with retry then success"""
        self.mock_func.side_effect = [Exception("Test error"), "success"]
        
        decorated_func = with_backoff(max_retries=3, initial_delay=1.0)(self.mock_func)
        
        result = decorated_func("arg1", kwarg1="value1")
        
        self.assertEqual(self.mock_func.call_count, 2)
        self.mock_func.assert_has_calls([
            call("arg1", kwarg1="value1"),
            call("arg1", kwarg1="value1")
        ])
        
        mock_sleep.assert_called_once()
        
        self.assertEqual(result, "success")
    
    @patch('time.sleep')
    def test_with_backoff_max_retries_exceeded(self, mock_sleep):
        """Test with_backoff decorator with max retries exceeded"""
        self.mock_func.side_effect = Exception("Test error")
        
        decorated_func = with_backoff(max_retries=2, initial_delay=1.0)(self.mock_func)
        
        with self.assertRaises(Exception):
            decorated_func("arg1", kwarg1="value1")
        
        self.assertEqual(self.mock_func.call_count, 3)  # Initial + 2 retries
        
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('time.sleep')
    @patch('random.random')
    def test_with_backoff_exponential_backoff(self, mock_random, mock_sleep):
        """Test with_backoff decorator with exponential backoff"""
        self.mock_func.side_effect = Exception("Test error")
        mock_random.return_value = 0.5  # 0.5 + 0.5 = 1.0 multiplier
        
        decorated_func = with_backoff(
            max_retries=2, 
            initial_delay=1.0, 
            exponential_base=2.0, 
            jitter=True
        )(self.mock_func)
        
        with self.assertRaises(Exception):
            decorated_func()
        
        mock_sleep.assert_has_calls([
            call(1.0),  # Initial delay * (0.5 + 0.5)
            call(2.0)   # Initial delay * 2^1 * (0.5 + 0.5)
        ])
    
    @patch('time.sleep')
    def test_with_backoff_specific_exceptions(self, mock_sleep):
        """Test with_backoff decorator with specific exceptions"""
        self.mock_func.side_effect = [
            ValueError("Value error"),  # Should be caught
            KeyError("Key error"),      # Should not be caught
            "success"
        ]
        
        decorated_func = with_backoff(
            max_retries=2, 
            initial_delay=1.0,
            exceptions=(ValueError,)
        )(self.mock_func)
        
        with self.assertRaises(KeyError):
            decorated_func()
        
        self.assertEqual(self.mock_func.call_count, 2)
        
        mock_sleep.assert_called_once()
    
    @patch('time.sleep')
    def test_with_backoff_max_delay(self, mock_sleep):
        """Test with_backoff decorator with max delay"""
        self.mock_func.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
            "success"
        ]
        
        decorated_func = with_backoff(
            max_retries=3, 
            initial_delay=10.0,
            max_delay=15.0,
            exponential_base=2.0,
            jitter=False
        )(self.mock_func)
        
        result = decorated_func()
        
        mock_sleep.assert_has_calls([
            call(10.0),  # Initial delay
            call(15.0),  # Capped at max_delay (would be 20.0)
            call(15.0)   # Capped at max_delay (would be 40.0)
        ])
        
        self.assertEqual(result, "success")


if __name__ == '__main__':
    unittest.main()
