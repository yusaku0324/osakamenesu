"""
Tests for twitter_client/composer.py
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from bot.services.twitter_client.composer import (
    find_textbox,
    type_text_cdp,
    type_text_clipboard,
    type_text_character,
    type_tweet_text,
    find_tweet_button,
    click_tweet_button
)


class TestComposerFunctions(unittest.TestCase):
    """Test Twitter composer functions"""
    
    def setUp(self):
        self.mock_driver = MagicMock(spec=WebDriver)
        self.mock_element = MagicMock(spec=WebElement)
        
        self.mock_driver.Keys = MagicMock()
        self.mock_driver.Keys.COMMAND = "cmd"
        self.mock_driver.Keys.CONTROL = "ctrl"
    
    @patch('bot.services.twitter_client.composer.WebDriverWait')
    def test_find_textbox_success(self, mock_wait):
        """Test successful textbox finding"""
        mock_wait.return_value.until.return_value = self.mock_element
        
        result = find_textbox(self.mock_driver)
        
        self.assertEqual(result, self.mock_element)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
    
    @patch('bot.services.twitter_client.composer.WebDriverWait')
    def test_find_textbox_failure(self, mock_wait):
        """Test textbox finding failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        
        result = find_textbox(self.mock_driver)
        
        self.assertIsNone(result)
    
    @patch('time.sleep')
    def test_type_text_cdp_success(self, mock_sleep):
        """Test successful CDP text input"""
        self.mock_driver.execute_cdp_cmd.return_value = None
        
        result = type_text_cdp(self.mock_driver, "Test text")
        
        self.assertTrue(result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": "Test text"}
        )
        mock_sleep.assert_called_once_with(0.3)
    
    @patch('time.sleep')
    def test_type_text_cdp_failure(self, mock_sleep):
        """Test CDP text input failure"""
        self.mock_driver.execute_cdp_cmd.side_effect = Exception("CDP error")
        
        result = type_text_cdp(self.mock_driver, "Test text")
        
        self.assertFalse(result)
    
    @patch('pyperclip.copy')
    @patch('time.sleep')
    def test_type_text_clipboard_success(self, mock_sleep, mock_copy):
        """Test successful clipboard text input"""
        self.mock_driver.Keys.COMMAND = "cmd"
        self.mock_driver.Keys.CONTROL = "ctrl"
        
        with patch('sys.platform', 'darwin'):
            result = type_text_clipboard(self.mock_driver, self.mock_element, "Test text")
        
        self.assertTrue(result)
        mock_copy.assert_called_once_with("Test text")
        self.mock_element.send_keys.assert_called_once_with("cmd", "v")
        mock_sleep.assert_called_once_with(0.3)
    
    @patch('pyperclip.copy')
    @patch('time.sleep')
    def test_type_text_clipboard_windows(self, mock_sleep, mock_copy):
        """Test clipboard text input on Windows"""
        self.mock_driver.Keys.CONTROL = "ctrl"
        
        with patch('sys.platform', 'win32'):
            result = type_text_clipboard(self.mock_driver, self.mock_element, "Test text")
        
        self.assertTrue(result)
        self.mock_element.send_keys.assert_called_once_with("ctrl", "v")
    
    @patch('pyperclip.copy')
    def test_type_text_clipboard_failure(self, mock_copy):
        """Test clipboard text input failure"""
        mock_copy.side_effect = Exception("Clipboard error")
        
        result = type_text_clipboard(self.mock_driver, self.mock_element, "Test text")
        
        self.assertFalse(result)
    
    @patch('time.sleep')
    @patch('random.uniform')
    def test_type_text_character_success(self, mock_uniform, mock_sleep):
        """Test successful character-by-character input"""
        mock_uniform.return_value = 0.03
        
        result = type_text_character(self.mock_element, "Test")
        
        self.assertTrue(result)
        self.assertEqual(self.mock_element.send_keys.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 4)
    
    def test_type_text_character_failure(self):
        """Test character-by-character input failure"""
        self.mock_element.send_keys.side_effect = Exception("Send keys error")
        
        result = type_text_character(self.mock_element, "Test")
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.composer.find_textbox')
    @patch('bot.services.twitter_client.composer.type_text_cdp')
    @patch('bot.services.twitter_client.composer.type_text_clipboard')
    @patch('bot.services.twitter_client.composer.type_text_character')
    @patch('time.sleep')
    def test_type_tweet_text_cdp_success(self, mock_sleep, mock_char, mock_clip, mock_cdp, mock_find):
        """Test tweet text input with CDP success"""
        mock_find.return_value = self.mock_element
        mock_cdp.return_value = True
        self.mock_element.text = "Test text"
        
        result = type_tweet_text(self.mock_driver, "Test text")
        
        self.assertTrue(result)
        mock_cdp.assert_called_once()
        mock_clip.assert_not_called()
        mock_char.assert_not_called()
    
    @patch('bot.services.twitter_client.composer.find_textbox')
    @patch('bot.services.twitter_client.composer.type_text_cdp')
    @patch('bot.services.twitter_client.composer.type_text_clipboard')
    @patch('bot.services.twitter_client.composer.type_text_character')
    @patch('time.sleep')
    def test_type_tweet_text_clipboard_fallback(self, mock_sleep, mock_char, mock_clip, mock_cdp, mock_find):
        """Test tweet text input with clipboard fallback"""
        mock_find.return_value = self.mock_element
        mock_cdp.return_value = False
        mock_clip.return_value = True
        self.mock_element.text = "Test text"
        
        result = type_tweet_text(self.mock_driver, "Test text")
        
        self.assertTrue(result)
        mock_cdp.assert_called_once()
        mock_clip.assert_called_once()
        mock_char.assert_not_called()
    
    @patch('bot.services.twitter_client.composer.find_textbox')
    @patch('bot.services.twitter_client.composer.type_text_cdp')
    @patch('bot.services.twitter_client.composer.type_text_clipboard')
    @patch('bot.services.twitter_client.composer.type_text_character')
    @patch('time.sleep')
    def test_type_tweet_text_character_fallback(self, mock_sleep, mock_char, mock_clip, mock_cdp, mock_find):
        """Test tweet text input with character fallback"""
        mock_find.return_value = self.mock_element
        mock_cdp.return_value = False
        mock_clip.return_value = False
        mock_char.return_value = True
        self.mock_element.text = ""
        
        result = type_tweet_text(self.mock_driver, "Test text")
        
        self.assertTrue(result)
        mock_cdp.assert_called_once()
        mock_clip.assert_called_once()
        mock_char.assert_called_once()
    
    @patch('bot.services.twitter_client.composer.find_textbox')
    def test_type_tweet_text_no_textbox(self, mock_find):
        """Test tweet text input with no textbox found"""
        mock_find.return_value = None
        
        result = type_tweet_text(self.mock_driver, "Test text")
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.composer.WebDriverWait')
    def test_find_tweet_button_success(self, mock_wait):
        """Test successful tweet button finding"""
        mock_wait.return_value.until.return_value = self.mock_element
        
        result = find_tweet_button(self.mock_driver)
        
        self.assertEqual(result, self.mock_element)
        mock_wait.assert_called_once_with(self.mock_driver, 15)
    
    @patch('bot.services.twitter_client.composer.WebDriverWait')
    def test_find_tweet_button_failure(self, mock_wait):
        """Test tweet button finding failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        
        result = find_tweet_button(self.mock_driver)
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.composer.find_tweet_button')
    @patch('time.sleep')
    def test_click_tweet_button_success(self, mock_sleep, mock_find):
        """Test successful tweet button click"""
        mock_find.return_value = self.mock_element
        
        result = click_tweet_button(self.mock_driver)
        
        self.assertTrue(result)
        self.mock_element.click.assert_called_once()
        mock_sleep.assert_called_once_with(5)
    
    @patch('bot.services.twitter_client.composer.find_tweet_button')
    def test_click_tweet_button_no_button(self, mock_find):
        """Test tweet button click with no button found"""
        mock_find.return_value = None
        
        result = click_tweet_button(self.mock_driver)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.composer.find_tweet_button')
    def test_click_tweet_button_click_error(self, mock_find):
        """Test tweet button click error"""
        mock_find.return_value = self.mock_element
        self.mock_element.click.side_effect = Exception("Click error")
        
        result = click_tweet_button(self.mock_driver)
        
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
