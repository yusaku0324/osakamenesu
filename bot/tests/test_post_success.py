"""
Tests for successful post creation with deduplication
"""
import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import os
import sqlite3

from bot.services.twitter_client.poster import post_to_twitter
from bot.utils.fingerprint import PostDeduplicator


class TestPostSuccess(unittest.TestCase):
    """Test successful post creation with deduplication"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.deduplicator = PostDeduplicator(self.temp_db.name)
        
        self.mock_driver = MagicMock()
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('bot.services.twitter_client.poster.wait_for_tweet_url')
    def test_post_success_with_deduplication(self, mock_wait_url, mock_click, mock_type, mock_navigate):
        """Test successful post with deduplication check"""
        mock_navigate.return_value = True
        mock_type.return_value = True
        mock_click.return_value = True
        mock_wait_url.return_value = "https://x.com/user/status/123456"
        
        test_text = "This is a test tweet #test"
        
        is_duplicate = self.deduplicator.is_duplicate(test_text)
        self.assertFalse(is_duplicate)
        
        result = post_to_twitter(self.mock_driver, test_text)
        self.assertEqual(result, "https://x.com/user/status/123456")
        
        success, fingerprint = self.deduplicator.add_post(test_text)
        self.assertTrue(success)
        
        is_duplicate = self.deduplicator.is_duplicate(test_text)
        self.assertTrue(is_duplicate)
        
        success, fingerprint = self.deduplicator.add_post(test_text)
        self.assertFalse(success)
    
    @patch('bot.services.twitter_client.poster.navigate_to_compose')
    @patch('bot.services.twitter_client.poster.prepare_media')
    @patch('bot.services.twitter_client.poster.upload_media')
    @patch('bot.services.twitter_client.poster.type_tweet_text')
    @patch('bot.services.twitter_client.poster.click_tweet_button')
    @patch('bot.services.twitter_client.poster.wait_for_tweet_url')
    def test_post_with_media_deduplication(self, mock_wait_url, mock_click, mock_type, mock_upload, mock_prepare, mock_navigate):
        """Test post with media and deduplication"""
        mock_navigate.return_value = True
        mock_prepare.return_value = "/tmp/test_media.png"
        mock_upload.return_value = True
        mock_type.return_value = True
        mock_click.return_value = True
        mock_wait_url.return_value = "https://x.com/user/status/789012"
        
        test_text = "This is a test tweet with media #test"
        test_media = "/tmp/test_media.png"
        
        with open(test_media, 'wb') as f:
            f.write(b"dummy media content")
        
        try:
            is_duplicate = self.deduplicator.is_duplicate(test_text, test_media)
            self.assertFalse(is_duplicate)
            
            result = post_to_twitter(self.mock_driver, test_text, media_url="https://example.com/media.png")
            self.assertEqual(result, "https://x.com/user/status/789012")
            
            success, fingerprint = self.deduplicator.add_post(test_text, test_media)
            self.assertTrue(success)
            
            is_duplicate = self.deduplicator.is_duplicate(test_text, test_media)
            self.assertTrue(is_duplicate)
            
            success, fingerprint = self.deduplicator.add_post(test_text, test_media)
            self.assertFalse(success)
        
        finally:
            if os.path.exists(test_media):
                os.unlink(test_media)
    
    def test_different_text_not_duplicate(self):
        """Test that different text is not considered duplicate"""
        text1 = "This is the first tweet #test"
        text2 = "This is the second tweet #test"
        
        success, fingerprint1 = self.deduplicator.add_post(text1)
        self.assertTrue(success)
        
        is_duplicate = self.deduplicator.is_duplicate(text2)
        self.assertFalse(is_duplicate)
        
        success, fingerprint2 = self.deduplicator.add_post(text2)
        self.assertTrue(success)
        
        self.assertNotEqual(fingerprint1, fingerprint2)
    
    def test_same_text_different_media_not_duplicate(self):
        """Test that same text with different media is not considered duplicate"""
        text = "This is a tweet with media #test"
        media1 = "/tmp/media1.png"
        media2 = "/tmp/media2.png"
        
        with open(media1, 'wb') as f:
            f.write(b"media content 1")
        with open(media2, 'wb') as f:
            f.write(b"media content 2")
        
        try:
            success, fingerprint1 = self.deduplicator.add_post(text, media1)
            self.assertTrue(success)
            
            is_duplicate = self.deduplicator.is_duplicate(text, media2)
            self.assertFalse(is_duplicate)
            
            success, fingerprint2 = self.deduplicator.add_post(text, media2)
            self.assertTrue(success)
            
            self.assertNotEqual(fingerprint1, fingerprint2)
        
        finally:
            if os.path.exists(media1):
                os.unlink(media1)
            if os.path.exists(media2):
                os.unlink(media2)


if __name__ == '__main__':
    unittest.main()
