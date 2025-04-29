"""
Tests for media.py
"""
import unittest
from unittest.mock import patch, MagicMock, call
import os
import tempfile
import subprocess

from bot.services.media import (
    create_video_from_image,
    create_combined_video,
    download_media,
    get_media_path
)


class TestMediaFunctions(unittest.TestCase):
    """Test media processing functions"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.temp_dir, "test_image.png")
        self.video_path = os.path.join(self.temp_dir, "test_video.mp4")
        self.combined_video_path = os.path.join(self.temp_dir, "combined_video.mp4")
        
        with open(self.image_path, 'w') as f:
            f.write("dummy image content")
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            for file in os.listdir(self.temp_dir):
                os.remove(os.path.join(self.temp_dir, file))
            os.rmdir(self.temp_dir)
    
    @patch('subprocess.run')
    def test_create_video_from_image_success(self, mock_run):
        """Test successful video creation from image"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = create_video_from_image(self.image_path, self.video_path)
        
        self.assertTrue(result)
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], 'ffmpeg')
        self.assertIn('-i', call_args)
        self.assertIn(self.image_path, call_args)
        self.assertIn(self.video_path, call_args)
    
    @patch('subprocess.run')
    def test_create_video_from_image_failure(self, mock_run):
        """Test video creation failure"""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        
        result = create_video_from_image(self.image_path, self.video_path)
        
        self.assertFalse(result)
    
    def test_create_video_from_image_missing_file(self):
        """Test video creation with missing input file"""
        result = create_video_from_image("nonexistent.png", self.video_path)
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_create_combined_video_success(self, mock_run):
        """Test successful video combination"""
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        video1 = os.path.join(self.temp_dir, "video1.mp4")
        video2 = os.path.join(self.temp_dir, "video2.mp4")
        with open(video1, 'w') as f:
            f.write("dummy video 1")
        with open(video2, 'w') as f:
            f.write("dummy video 2")
        
        result = create_combined_video([video1, video2], self.combined_video_path)
        
        self.assertTrue(result)
        mock_run.assert_called_once()
        
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], 'ffmpeg')
        self.assertIn('-f', call_args)
        self.assertIn('concat', call_args)
    
    @patch('subprocess.run')
    def test_create_combined_video_failure(self, mock_run):
        """Test video combination failure"""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error")
        
        video1 = os.path.join(self.temp_dir, "video1.mp4")
        with open(video1, 'w') as f:
            f.write("dummy video 1")
        
        result = create_combined_video([video1], self.combined_video_path)
        
        self.assertFalse(result)
    
    def test_create_combined_video_empty_list(self):
        """Test video combination with empty list"""
        result = create_combined_video([], self.combined_video_path)
        
        self.assertFalse(result)
    
    def test_create_combined_video_missing_file(self):
        """Test video combination with missing file"""
        result = create_combined_video(["nonexistent.mp4"], self.combined_video_path)
        
        self.assertFalse(result)
    
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
        
        self.assertTrue(result)
        mock_urlretrieve.assert_called_once_with(url, output_path)
    
    @patch('urllib.request.urlretrieve')
    def test_download_media_failure(self, mock_urlretrieve):
        """Test media download failure"""
        url = "https://example.com/image.png"
        output_path = os.path.join(self.temp_dir, "downloaded.png")
        
        mock_urlretrieve.side_effect = Exception("Download failed")
        
        result = download_media(url, output_path)
        
        self.assertFalse(result)
    
    def test_download_media_invalid_url(self):
        """Test media download with invalid URL"""
        result = download_media("invalid_url", self.video_path)
        
        self.assertFalse(result)
    
    @patch('bot.services.media.download_media')
    def test_get_media_path_local_file(self, mock_download):
        """Test get_media_path with local file"""
        result = get_media_path(self.image_path, "output.png")
        
        self.assertEqual(result, self.image_path)
        mock_download.assert_not_called()
    
    @patch('bot.services.media.download_media')
    def test_get_media_path_url_success(self, mock_download):
        """Test get_media_path with URL"""
        mock_download.return_value = True
        url = "https://example.com/image.png"
        local_filename = "output.png"
        
        result = get_media_path(url, local_filename)
        
        self.assertEqual(result, local_filename)
        mock_download.assert_called_once_with(url, local_filename)
    
    @patch('bot.services.media.download_media')
    def test_get_media_path_url_failure(self, mock_download):
        """Test get_media_path with URL download failure"""
        mock_download.return_value = False
        url = "https://example.com/image.png"
        local_filename = "output.png"
        
        result = get_media_path(url, local_filename)
        
        self.assertIsNone(result)
    
    def test_get_media_path_empty_url(self):
        """Test get_media_path with empty URL"""
        result = get_media_path("", "output.png")
        
        self.assertIsNone(result)
    
    def test_get_media_path_invalid_format(self):
        """Test get_media_path with invalid format"""
        result = get_media_path("invalid_format", "output.png")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
