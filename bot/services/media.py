"""
Media services for the bot
"""
import logging
import os
import subprocess
import tempfile
import urllib.request
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def create_video_from_image(image_path: str, output_path: str, duration: int = 5) -> bool:
    """
    Create a video from a static image
    
    Args:
        image_path: Path to the input image
        output_path: Path to save the output video
        duration: Duration of the video in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating video from image: {e}")
        return False


def create_combined_video(video_paths: List[str], output_path: str) -> bool:
    """
    Combine multiple videos into one
    
    Args:
        video_paths: List of paths to input videos
        output_path: Path to save the output video
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not video_paths:
            logger.error("No video paths provided")
            return False
        
        for path in video_paths:
            if not os.path.exists(path):
                logger.error(f"Video file not found: {path}")
                return False
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")
            concat_file = f.name
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
            
            return True
        
        finally:
            os.remove(concat_file)
    
    except Exception as e:
        logger.error(f"Error combining videos: {e}")
        return False


def download_media(url: str, output_path: str) -> bool:
    """
    Download media from a URL
    
    Args:
        url: URL to download from
        output_path: Path to save the downloaded file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL: {url}")
            return False
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        logger.info(f"Downloading media from {url} to {output_path}")
        urllib.request.urlretrieve(url, output_path)
        
        if not os.path.exists(output_path):
            logger.error(f"Download failed: {output_path} not found")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error downloading media: {e}")
        return False


def get_media_path(media_url: str, local_path: str) -> Optional[str]:
    """
    Get the path to a media file, downloading it if necessary
    
    Args:
        media_url: URL or local path to the media
        local_path: Path to save the media if downloading
        
    Returns:
        Optional[str]: Path to the media file, or None if failed
    """
    try:
        if not media_url:
            logger.error("No media URL provided")
            return None
        
        if os.path.exists(media_url):
            return media_url
        
        if media_url.startswith(('http://', 'https://')):
            if download_media(media_url, local_path):
                return local_path
            else:
                logger.error(f"Failed to download media from {media_url}")
                return None
        
        logger.error(f"Unrecognized media URL format: {media_url}")
        return None
    
    except Exception as e:
        logger.error(f"Error getting media path: {e}")
        return None


def extract_text_from_media(media_path: str, media_type: str = 'auto') -> Dict[str, Any]:
    """
    Extract text from media using OCR
    
    Args:
        media_path: Path to the media file
        media_type: Type of media ('image', 'video', or 'auto')
        
    Returns:
        Dict[str, Any]: Extracted text and metadata
    """
    try:
        from bot.utils.ocr import extract_text_from_image, extract_text_from_video
        
        if not os.path.exists(media_path):
            logger.error(f"Media file not found: {media_path}")
            return {'success': False, 'error': 'File not found'}
        
        if media_type == 'auto':
            ext = os.path.splitext(media_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                media_type = 'image'
            elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                media_type = 'video'
            else:
                logger.error(f"Unsupported media type: {ext}")
                return {'success': False, 'error': f'Unsupported media type: {ext}'}
        
        if media_type == 'image':
            text = extract_text_from_image(media_path)
            return {'success': True, 'text': text, 'type': 'image'}
        
        elif media_type == 'video':
            results = extract_text_from_video(media_path)
            return {'success': True, 'results': results, 'type': 'video'}
        
        else:
            logger.error(f"Invalid media type: {media_type}")
            return {'success': False, 'error': f'Invalid media type: {media_type}'}
    
    except Exception as e:
        logger.error(f"Error extracting text from media: {e}")
        return {'success': False, 'error': str(e)}


def extract_text_from_media_url(media_url: str, media_type: str = 'auto') -> Dict[str, Any]:
    """
    Extract text from media URL using OCR
    
    Args:
        media_url: URL to the media file
        media_type: Type of media ('image', 'video', or 'auto')
        
    Returns:
        Dict[str, Any]: Extracted text and metadata
    """
    try:
        ext = os.path.splitext(media_url)[1] or '.tmp'
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            if not download_media(media_url, tmp_path):
                return {'success': False, 'error': 'Failed to download media'}
            
            result = extract_text_from_media(tmp_path, media_type)
            return result
        
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except Exception as e:
        logger.error(f"Error extracting text from media URL: {e}")
        return {'success': False, 'error': str(e)}


def extract_text_from_video_frames(video_path: str, frame_numbers: List[int] = None) -> Dict[str, Any]:
    """
    Extract text from specific frames of a video
    
    Args:
        video_path: Path to the video file
        frame_numbers: List of frame numbers to extract text from
        
    Returns:
        Dict[str, Any]: Extracted text and metadata
    """
    try:
        from bot.utils.ocr import extract_text_from_video_frame
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {'success': False, 'error': 'File not found'}
        
        results = []
        
        if frame_numbers:
            for frame_num in frame_numbers:
                text = extract_text_from_video_frame(video_path, frame_num)
                results.append({'frame': frame_num, 'text': text})
        else:
            from bot.utils.ocr import extract_text_from_video
            results = extract_text_from_video(video_path, frame_interval=30)
        
        return {'success': True, 'results': results, 'type': 'video'}
    
    except Exception as e:
        logger.error(f"Error extracting text from video frames: {e}")
        return {'success': False, 'error': str(e)}
