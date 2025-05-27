"""
Tests for twitter_client/poster.py
"""
import unittest
from unittest.mock import patch, MagicMock, call
import time
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

from bot.services.twitter_client.poster import (
    navigate_to_compose,
    wait_for_tweet_url,
    post_to_twitter,
    extract_tweet_id,
    navigate_to_tweet,
    find_reply_button,
    reply_to_tweet
)


class TestPosterFunctions(unittest.TestCase):
    """Test Twitter poster functions"""
    
    def setUp(self):
        self.mock_driver = MagicMock(spec=WebDriver)
        self.mock_logger = MagicMock(spec=logging.Logger)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_navigate_to_compose_success(self, mock_wait):
        """Test successful navigation to compose"""
        mock_wait.return_value.until.return_value = MagicMock()
        
        result = navigate_to_compose(self.mock_driver)
        
        self.assertTrue(result)
        self.mock_driver.get.assert_called_once_with("https://x.com/compose/tweet")
        mock_wait.assert_called_once_with(self.mock_driver, 15)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_navigate_to_compose_failure(self, mock_wait):
        """Test navigation to compose failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        
        result = navigate_to_compose(self.mock_driver)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_wait_for_tweet_url_success(self, mock_wait):
        """Test successful tweet URL wait"""
        self.mock_driver.current_url = "https://x.com/user/status/123456"
        mock_wait.return_value.until.return_value = True
        
        result = wait_for_tweet_url(self.mock_driver)
        
        self.assertEqual(result, "https://x.com/user/status/123456")
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_wait_for_tweet_url_fallback(self, mock_wait):
        """Test tweet URL wait with fallback"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        mock_element = MagicMock()
        mock_element.get_attribute.return_value = "https://x.com/user/status/123456"
        self.mock_driver.find_element.return_value = mock_element
        
        result = wait_for_tweet_url(self.mock_driver)
        
        self.assertEqual(result, "https://x.com/user/status/123456")
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_wait_for_tweet_url_failure(self, mock_wait):
        """Test tweet URL wait failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        self.mock_driver.find_element.side_effect = Exception("Not found")
        
        result = wait_for_tweet_url(self.mock_driver)
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('bot.services.twitter_client.poster.wait_for_tweet_url')
    @patch('time.sleep')
    def test_post_to_twitter_success(self, mock_sleep, mock_wait_url, mock_click, mock_type, mock_navigate):
        """Test successful Twitter post"""
        mock_navigate.return_value = True
        mock_type.return_value = True
        mock_click.return_value = True
        mock_wait_url.return_value = "https://x.com/user/status/123456"
        
        result = post_to_twitter(self.mock_driver, "Test tweet")
        
        self.assertEqual(result, "https://x.com/user/status/123456")
        mock_navigate.assert_called_once()
        mock_type.assert_called_once_with(self.mock_driver, "Test tweet")
        mock_click.assert_called_once()
        mock_wait_url.assert_called_once()
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    def test_post_to_twitter_navigate_failure(self, mock_navigate):
        """Test Twitter post with navigation failure"""
        mock_navigate.return_value = False
        
        result = post_to_twitter(self.mock_driver, "Test tweet")
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('time.sleep')
    def test_post_to_twitter_type_failure(self, mock_sleep, mock_type, mock_navigate):
        """Test Twitter post with type failure"""
        mock_navigate.return_value = True
        mock_type.return_value = False
        
        result = post_to_twitter(self.mock_driver, "Test tweet")
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('time.sleep')
    def test_post_to_twitter_click_failure(self, mock_sleep, mock_click, mock_type, mock_navigate):
        """Test Twitter post with click failure"""
        mock_navigate.return_value = True
        mock_type.return_value = True
        mock_click.return_value = False
        
        result = post_to_twitter(self.mock_driver, "Test tweet")
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.prepare_media')
    @patch('bot.services.twitter_client.poster.upload_media')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('bot.services.twitter_client.poster.wait_for_tweet_url')
    @patch('time.sleep')
    def test_post_to_twitter_with_media(self, mock_sleep, mock_wait_url, mock_click, mock_type, mock_upload, mock_prepare, mock_navigate):
        """Test Twitter post with media"""
        mock_navigate.return_value = True
        mock_prepare.return_value = "media.png"
        mock_upload.return_value = True
        mock_type.return_value = True
        mock_click.return_value = True
        mock_wait_url.return_value = "https://x.com/user/status/123456"
        
        result = post_to_twitter(self.mock_driver, "Test tweet", media_url="https://example.com/media.png")
        
        self.assertEqual(result, "https://x.com/user/status/123456")
        mock_prepare.assert_called_once_with("https://example.com/media.png")
        mock_upload.assert_called_once_with(self.mock_driver, "media.png")
    
    def test_extract_tweet_id_success(self):
        """Test successful tweet ID extraction"""
        tweet_url = "https://x.com/user/status/123456"
        
        result = extract_tweet_id(tweet_url)
        
        self.assertEqual(result, "123456")
    
    def test_extract_tweet_id_no_status(self):
        """Test tweet ID extraction with no status"""
        tweet_url = "https://x.com/user"
        
        result = extract_tweet_id(tweet_url)
        
        self.assertIsNone(result)
    
    def test_extract_tweet_id_empty_url(self):
        """Test tweet ID extraction with empty URL"""
        result = extract_tweet_id("")
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_navigate_to_tweet_success(self, mock_wait):
        """Test successful navigation to tweet"""
        mock_wait.return_value.until.return_value = MagicMock()
        tweet_url = "https://x.com/user/status/123456"
        
        result = navigate_to_tweet(self.mock_driver, tweet_url)
        
        self.assertTrue(result)
        self.mock_driver.get.assert_called_once_with(tweet_url)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_navigate_to_tweet_failure(self, mock_wait):
        """Test navigation to tweet failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        tweet_url = "https://x.com/user/status/123456"
        
        result = navigate_to_tweet(self.mock_driver, tweet_url)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    @patch('time.sleep')
    def test_find_reply_button_success(self, mock_sleep, mock_wait):
        """Test successful reply button finding"""
        mock_button = MagicMock()
        mock_wait.return_value.until.side_effect = [mock_button, MagicMock()]
        
        result = find_reply_button(self.mock_driver)
        
        self.assertTrue(result)
        mock_button.click.assert_called_once()
        self.assertEqual(mock_wait.call_count, 2)
    
    @patch('bot.services.twitter_client.poster.WebDriverWait')
    def test_find_reply_button_failure(self, mock_wait):
        """Test reply button finding failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        
        result = find_reply_button(self.mock_driver)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_tweet')
    @patch('bot.services.twitter_client.poster.find_reply_button')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('bot.services.twitter_client.poster.wait_for_tweet_url')
    @patch('time.sleep')
    def test_reply_to_tweet_success(self, mock_sleep, mock_wait_url, mock_click, mock_type, mock_find_reply, mock_navigate):
        """Test successful tweet reply"""
        mock_navigate.return_value = True
        mock_find_reply.return_value = True
        mock_type.return_value = True
        mock_click.return_value = True
        mock_wait_url.return_value = "https://x.com/user/status/789012"
        
        result = reply_to_tweet(self.mock_driver, "https://x.com/user/status/123456", "Test reply")
        
        self.assertEqual(result, "https://x.com/user/status/789012")
        mock_navigate.assert_called_once_with(self.mock_driver, "https://x.com/user/status/123456")
        mock_find_reply.assert_called_once()
        mock_type.assert_called_once_with(self.mock_driver, "Test reply")
        mock_click.assert_called_once()
        mock_wait_url.assert_called_once()
    
    @patch('bot.services.twitter_client.poster.navigate_to_tweet')
    def test_reply_to_tweet_navigate_failure(self, mock_navigate):
        """Test tweet reply with navigation failure"""
        mock_navigate.return_value = False
        
        result = reply_to_tweet(self.mock_driver, "https://x.com/user/status/123456", "Test reply")
        
        self.assertIsNone(result)
    
    @patch('bot.services.twitter_client.poster.navigate_to_tweet')
    @patch('bot.services.twitter_client.poster.find_reply_button')
    @patch('time.sleep')
    def test_reply_to_tweet_find_button_failure(self, mock_sleep, mock_find_reply, mock_navigate):
        """Test tweet reply with find button failure"""
        mock_navigate.return_value = True
        mock_find_reply.return_value = False
        
        result = reply_to_tweet(self.mock_driver, "https://x.com/user/status/123456", "Test reply")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
