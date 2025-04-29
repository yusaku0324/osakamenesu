"""
Tests for cookie_loader.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

from bot.services.twitter_client.cookie_loader import (
    load_cookies,
    save_cookies,
    validate_cookies
)


class TestCookieLoaderFunctions(unittest.TestCase):
    """Test cookie loader functions"""
    
    def setUp(self):
        self.mock_driver = MagicMock()
        self.cookie_data = [
            {
                'name': 'auth_token',
                'value': 'test_token',
                'domain': '.x.com',
                'path': '/',
                'secure': False,
                'sameSite': 'Lax'
            },
            {
                'name': 'ct0',
                'value': 'test_ct0',
                'domain': '.x.com',
                'path': '/',
                'secure': False,
                'sameSite': 'Lax',
                'expiry': 1234567890
            }
        ]
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_cookies_success(self, mock_json_load, mock_file, mock_exists):
        """Test successful cookie loading"""
        mock_exists.return_value = True
        mock_json_load.return_value = self.cookie_data
        
        result = load_cookies(self.mock_driver, "/path/to/cookies.json")
        
        self.assertTrue(result)
        self.mock_driver.get.assert_called_once_with("https://x.com/home")
        self.mock_driver.delete_all_cookies.assert_called_once()
        self.assertEqual(self.mock_driver.add_cookie.call_count, 2)
        self.mock_driver.refresh.assert_called_once()
        
        for call in self.mock_driver.add_cookie.call_args_list:
            cookie = call[0][0]
            self.assertEqual(cookie['sameSite'], 'None')
            self.assertTrue(cookie['secure'])
            self.assertNotIn('expiry', cookie)
    
    @patch('os.path.exists')
    def test_load_cookies_file_not_found(self, mock_exists):
        """Test cookie loading with non-existent file"""
        mock_exists.return_value = False
        
        result = load_cookies(self.mock_driver, "/path/to/nonexistent.json")
        
        self.assertFalse(result)
        self.mock_driver.get.assert_not_called()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_cookies_add_cookie_error(self, mock_json_load, mock_file, mock_exists):
        """Test cookie loading with add_cookie error"""
        mock_exists.return_value = True
        mock_json_load.return_value = self.cookie_data
        self.mock_driver.add_cookie.side_effect = Exception("Add cookie error")
        
        result = load_cookies(self.mock_driver, "/path/to/cookies.json")
        
        self.assertTrue(result)  # Still returns True even if some cookies fail
        self.mock_driver.refresh.assert_called_once()
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_load_cookies_json_error(self, mock_json_load, mock_file, mock_exists):
        """Test cookie loading with JSON error"""
        mock_exists.return_value = True
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        result = load_cookies(self.mock_driver, "/path/to/cookies.json")
        
        self.assertFalse(result)
    
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_cookies_success(self, mock_json_dump, mock_file, mock_makedirs):
        """Test successful cookie saving"""
        self.mock_driver.get_cookies.return_value = self.cookie_data
        
        result = save_cookies(self.mock_driver, "/path/to/cookies.json")
        
        self.assertTrue(result)
        self.mock_driver.get_cookies.assert_called_once()
        mock_makedirs.assert_called_once_with(os.path.dirname("/path/to/cookies.json"), exist_ok=True)
        mock_json_dump.assert_called_once()
    
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_cookies_error(self, mock_file, mock_makedirs):
        """Test cookie saving with error"""
        self.mock_driver.get_cookies.side_effect = Exception("Get cookies error")
        
        result = save_cookies(self.mock_driver, "/path/to/cookies.json")
        
        self.assertFalse(result)
    
    def test_validate_cookies_valid(self):
        """Test cookie validation with valid cookies"""
        result = validate_cookies(self.cookie_data)
        self.assertTrue(result)
    
    def test_validate_cookies_missing_field(self):
        """Test cookie validation with missing field"""
        invalid_cookies = [
            {
                'name': 'auth_token',
                'value': 'test_token'
            }
        ]
        
        result = validate_cookies(invalid_cookies)
        self.assertFalse(result)
    
    def test_validate_cookies_empty_list(self):
        """Test cookie validation with empty list"""
        result = validate_cookies([])
        self.assertTrue(result)  # Empty list is considered valid


if __name__ == '__main__':
    unittest.main()
