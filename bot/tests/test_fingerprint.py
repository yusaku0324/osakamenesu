"""
Tests for fingerprint.py
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sqlite3
import tempfile
import hashlib

from bot.utils.fingerprint import PostDeduplicator


class TestPostDeduplicator(unittest.TestCase):
    """Test PostDeduplicator class"""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.deduplicator = PostDeduplicator(self.temp_db.name)
    
    def tearDown(self):
        os.unlink(self.temp_db.name)
    
    def test_init_db(self):
        """Test database initialization"""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_normalize_text(self):
        """Test text normalization"""
        text = "  Hello   World  "
        normalized = self.deduplicator._normalize_text(text)
        self.assertEqual(normalized, "hello world")
        
        text = "Hello！ World？"
        normalized = self.deduplicator._normalize_text(text)
        self.assertEqual(normalized, "hello! world?")
    
    def test_generate_fingerprint_text_only(self):
        """Test fingerprint generation with text only"""
        text = "Hello World"
        fingerprint = self.deduplicator.generate_fingerprint(text)
        
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 64)  # SHA256 hex digest length
        
        fingerprint2 = self.deduplicator.generate_fingerprint(text)
        self.assertEqual(fingerprint, fingerprint2)
        
        fingerprint3 = self.deduplicator.generate_fingerprint("Different text")
        self.assertNotEqual(fingerprint, fingerprint3)
    
    def test_generate_fingerprint_with_media(self):
        """Test fingerprint generation with text and media"""
        text = "Hello World"
        media_hash = "abcd1234"
        fingerprint = self.deduplicator.generate_fingerprint(text, media_hash)
        
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 64)
        
        fingerprint_without_media = self.deduplicator.generate_fingerprint(text)
        self.assertNotEqual(fingerprint, fingerprint_without_media)
    
    def test_is_duplicate_false(self):
        """Test is_duplicate returns False for new post"""
        result = self.deduplicator.is_duplicate("New post")
        self.assertFalse(result)
    
    def test_is_duplicate_true(self):
        """Test is_duplicate returns True for duplicate post"""
        self.deduplicator.add_post("Test post")
        
        result = self.deduplicator.is_duplicate("Test post")
        self.assertTrue(result)
    
    def test_add_post_success(self):
        """Test successful post addition"""
        success, fingerprint = self.deduplicator.add_post("New post")
        
        self.assertTrue(success)
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 64)
    
    def test_add_post_duplicate(self):
        """Test adding duplicate post"""
        self.deduplicator.add_post("Test post")
        
        success, fingerprint = self.deduplicator.add_post("Test post")
        
        self.assertFalse(success)
        self.assertIsInstance(fingerprint, str)
    
    def test_add_post_with_media(self):
        """Test adding post with media"""
        success, fingerprint = self.deduplicator.add_post("Post with media", "media_hash_123")
        
        self.assertTrue(success)
        self.assertIsInstance(fingerprint, str)
    
    def test_remove_post(self):
        """Test removing a post"""
        success, fingerprint = self.deduplicator.add_post("Test post")
        self.assertTrue(success)
        
        removed = self.deduplicator.remove_post(fingerprint)
        self.assertTrue(removed)
        
        is_duplicate = self.deduplicator.is_duplicate("Test post")
        self.assertFalse(is_duplicate)
    
    def test_clear_database(self):
        """Test clearing the database"""
        self.deduplicator.add_post("Post 1")
        self.deduplicator.add_post("Post 2")
        
        cleared = self.deduplicator.clear_database()
        self.assertTrue(cleared)
        
        self.assertFalse(self.deduplicator.is_duplicate("Post 1"))
        self.assertFalse(self.deduplicator.is_duplicate("Post 2"))





if __name__ == '__main__':
    unittest.main()
