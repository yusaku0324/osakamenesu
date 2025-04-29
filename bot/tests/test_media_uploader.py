"""
Tests for twitter_client/media_uploader.py
"""
import unittest
import pytest
from unittest.mock import patch, MagicMock, call
import os
import tempfile
import urllib.request

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

from bot.services.twitter_client.media_uploader import (
    download_media,
    find_media_button,
    upload_media,
    upload_multiple_media,
    prepare_media,
    VIDEO_EXTS,
    MAX_TOTAL,
    MAX_VIDEOS
)


class TestMediaUploaderFunctions(unittest.TestCase):
    """Test media uploader functions"""
    
    def setUp(self):
        self.mock_driver = MagicMock(spec=WebDriver)
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.png")
        
        with open(self.test_file, 'w') as f:
            f.write("test content")
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
    
    @patch('urllib.request.urlretrieve')
    def test_download_media_success(self, mock_urlretrieve):
        """Test successful media download"""
        url = "https://example.com/image.png"
        output_path = os.path.join(self.temp_dir, "downloaded.png")
        
        def side_effect(url, path):
            with open(path, 'w') as f:
                f.write("downloaded content")
        
        mock_urlretrieve.side_effect = side_effect
        
        result = download_media(url, output_path)
        
        self.assertEqual(result, output_path)
        mock_urlretrieve.assert_called_once_with(url, output_path)
    
    @patch('urllib.request.urlretrieve')
    def test_download_media_failure(self, mock_urlretrieve):
        """Test media download failure"""
        url = "https://example.com/image.png"
        output_path = os.path.join(self.temp_dir, "downloaded.png")
        
        mock_urlretrieve.side_effect = Exception("Download failed")
        
        result = download_media(url, output_path)
        
        self.assertIsNone(result)
    
    def test_download_media_local_file(self):
        """Test download_media with local file"""
        result = download_media(self.test_file)
        
        self.assertEqual(result, self.test_file)
    
    def test_download_media_invalid_url(self):
        """Test download_media with invalid URL"""
        result = download_media("invalid_url")
        
        self.assertIsNone(result)
    
    @patch('tempfile.mkstemp')
    @patch('urllib.request.urlretrieve')
    @patch('os.close')
    def test_download_media_no_output_path(self, mock_close, mock_urlretrieve, mock_mkstemp):
        """Test download_media without output path"""
        url = "https://example.com/image.png"
        temp_path = os.path.join(self.temp_dir, "temp.png")
        
        with open(temp_path, 'w') as f:
            f.write("")
        
        mock_mkstemp.return_value = (999, temp_path)
        
        def side_effect(url, path):
            with open(path, 'w') as f:
                f.write("downloaded content")
        
        mock_urlretrieve.side_effect = side_effect
        
        result = download_media(url)
        
        self.assertEqual(result, temp_path)
        mock_close.assert_called_once_with(999)
    
    @patch('bot.services.twitter_client.media_uploader.WebDriverWait')
    def test_find_media_button_success(self, mock_wait):
        """Test successful media button finding"""
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element
        
        result = find_media_button(self.mock_driver)
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
    
    @patch('bot.services.twitter_client.media_uploader.WebDriverWait')
    def test_find_media_button_failure(self, mock_wait):
        """Test media button finding failure"""
        mock_wait.return_value.until.side_effect = Exception("Timeout")
        
        result = find_media_button(self.mock_driver)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.media_uploader.find_media_button')
    @patch('bot.services.twitter_client.media_uploader.WebDriverWait')
    def test_upload_media_success(self, mock_wait, mock_find_button):
        """Test successful media upload"""
        mock_find_button.return_value = True
        mock_file_input = MagicMock()
        self.mock_driver.find_element.return_value = mock_file_input
        mock_wait.return_value.until.return_value = MagicMock()
        
        result = upload_media(self.mock_driver, self.test_file)
        
        self.assertTrue(result)
        mock_file_input.send_keys.assert_called_once_with(os.path.abspath(self.test_file))
    
    @patch('bot.services.twitter_client.media_uploader.find_media_button')
    def test_upload_media_no_button(self, mock_find_button):
        """Test media upload with no button found"""
        mock_find_button.return_value = False
        
        result = upload_media(self.mock_driver, self.test_file)
        
        self.assertFalse(result)
    
    def test_upload_media_file_not_found(self):
        """Test media upload with non-existent file"""
        result = upload_media(self.mock_driver, "nonexistent.png")
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.media_uploader.find_media_button')
    @patch('bot.services.twitter_client.media_uploader.WebDriverWait')
    def test_upload_media_upload_failure(self, mock_wait, mock_find_button):
        """Test media upload failure"""
        mock_find_button.return_value = True
        mock_file_input = MagicMock()
        self.mock_driver.find_element.return_value = mock_file_input
        mock_wait.return_value.until.side_effect = Exception("Upload failed")
        
        result = upload_media(self.mock_driver, self.test_file)
        
        self.assertFalse(result)
    
    @patch('bot.services.twitter_client.media_uploader.upload_media')
    @patch('time.sleep')
    def test_upload_multiple_media_success(self, mock_sleep, mock_upload):
        """Test successful multiple media upload"""
        mock_upload.return_value = True
        media_paths = [self.test_file, self.test_file]
        
        result = upload_multiple_media(self.mock_driver, media_paths)
        
        self.assertTrue(result)
        self.assertEqual(mock_upload.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('bot.services.twitter_client.media_uploader.upload_media')
    def test_upload_multiple_media_partial_failure(self, mock_upload):
        """Test multiple media upload with partial failure"""
        mock_upload.side_effect = [True, False]
        media_paths = [self.test_file, "nonexistent.png"]
        
        result = upload_multiple_media(self.mock_driver, media_paths)
        
        self.assertFalse(result)
    
    def test_upload_multiple_media_empty_list(self):
        """Test multiple media upload with empty list"""
        result = upload_multiple_media(self.mock_driver, [])
        
        self.assertTrue(result)
    
    def test_prepare_media_local_file(self):
        """Test prepare_media with local file"""
        result = prepare_media(self.test_file)
        
        self.assertEqual(result, self.test_file)
    
    @patch('bot.services.twitter_client.media_uploader.download_media')
    def test_prepare_media_url(self, mock_download):
        """Test prepare_media with URL"""
        url = "https://example.com/image.png"
        mock_download.return_value = "downloaded.png"
        
        result = prepare_media(url)
        
        self.assertEqual(result, "downloaded.png")
        mock_download.assert_called_once_with(url)
    
    def test_prepare_media_empty_url(self):
        """Test prepare_media with empty URL"""
        result = prepare_media("")
        
        self.assertIsNone(result)
    
    def test_prepare_media_invalid_format(self):
        """Test prepare_media with invalid format"""
        result = prepare_media("invalid_format")
        
        self.assertIsNone(result)
    
    @patch("bot.services.twitter_client.media_uploader.upload_media")
    @patch("time.sleep")
    def test_upload_multiple_media_four_videos_success(self, mock_sleep, mock_upload):
        """4 本動画は許可される"""
        mock_upload.return_value = True
        media_paths = [f"video{i}.mp4" for i in range(4)]
        result = upload_multiple_media(MagicMock(), media_paths)
        assert result is True
        assert mock_upload.call_count == 4
    
    @patch("bot.services.twitter_client.media_uploader.upload_media")
    def test_upload_multiple_media_total_limit_exceeded(self, mock_upload):
        """添付 5 件なら False"""
        media_paths = [f"img{i}.png" for i in range(5)]
        result = upload_multiple_media(MagicMock(), media_paths)
        assert result is False
        mock_upload.assert_not_called()
    
    @patch("bot.services.twitter_client.media_uploader.upload_media")
    def test_upload_multiple_media_video_limit_exceeded(self, mock_upload):
        """動画 5 本なら False"""
        media_paths = [f"video{i}.mp4" for i in range(5)]
        result = upload_multiple_media(MagicMock(), media_paths)
        assert result is False
        mock_upload.assert_not_called()


if __name__ == '__main__':
    unittest.main()
