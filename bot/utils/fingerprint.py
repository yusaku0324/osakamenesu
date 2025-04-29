"""
Fingerprint utility for deduplication
"""
import hashlib
import logging
import os
import sqlite3
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)


class PostDeduplicator:
    """
    Deduplicator for posts using SHA256 fingerprinting and SQLite storage
    """
    
    def __init__(self, db_path: str = "posts.db"):
        """
        Initialize the deduplicator with a SQLite database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS posts (
                        fingerprint TEXT PRIMARY KEY,
                        text TEXT NOT NULL,
                        media_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logger.info(f"Initialized deduplication database at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def generate_fingerprint(self, text: str, media_hash: Optional[str] = None) -> str:
        """
        Generate a SHA256 fingerprint for a post
        
        Args:
            text: Post text content
            media_hash: Optional hash of media content
            
        Returns:
            SHA256 fingerprint string
        """
        normalized_text = self._normalize_text(text)
        content = normalized_text
        
        if media_hash:
            content += f"|{media_hash}"
        
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent fingerprinting
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        text = ' '.join(text.split())
        text = text.lower()
        text = text.replace('！', '!').replace('？', '?')
        return text
    
    def is_duplicate(self, text: str, media_hash: Optional[str] = None) -> bool:
        """
        Check if a post is a duplicate
        
        Args:
            text: Post text content
            media_hash: Optional hash of media content
            
        Returns:
            True if duplicate, False otherwise
        """
        fingerprint = self.generate_fingerprint(text, media_hash)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM posts WHERE fingerprint = ?", (fingerprint,))
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Error checking for duplicate: {e}")
            return False
    
    def add_post(self, text: str, media_hash: Optional[str] = None) -> Tuple[bool, str]:
        """
        Add a post to the deduplication database
        
        Args:
            text: Post text content
            media_hash: Optional hash of media content
            
        Returns:
            Tuple of (success, fingerprint)
        """
        fingerprint = self.generate_fingerprint(text, media_hash)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO posts (fingerprint, text, media_hash) VALUES (?, ?, ?)",
                    (fingerprint, text, media_hash)
                )
                conn.commit()
                logger.info(f"Added post with fingerprint: {fingerprint}")
                return True, fingerprint
        except sqlite3.IntegrityError:
            logger.warning(f"Post already exists with fingerprint: {fingerprint}")
            return False, fingerprint
        except Exception as e:
            logger.error(f"Error adding post: {e}")
            return False, fingerprint
    
    def remove_post(self, fingerprint: str) -> bool:
        """
        Remove a post from the deduplication database
        
        Args:
            fingerprint: Fingerprint of post to remove
            
        Returns:
            True if removed, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM posts WHERE fingerprint = ?", (fingerprint,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing post: {e}")
            return False
    
    def clear_database(self) -> bool:
        """
        Clear all posts from the database
        
        Returns:
            True if cleared, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM posts")
                conn.commit()
                logger.info("Cleared all posts from database")
                return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
