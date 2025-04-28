"""
Tests for Chrome DevTools Protocol utilities
"""
import unittest
from unittest.mock import MagicMock, patch
import pytest

from bot.utils.cdp import insert_text


class TestCDPUtils(unittest.TestCase):
    """Test CDP utilities"""
    
    def setUp(self):
        self.mock_driver = MagicMock()
    
    def test_insert_text_success(self):
        """Test successful text insertion"""
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, "test text")
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": "test text"}
        )
    
    def test_insert_text_long_text(self):
        """Test insertion of long text"""
        long_text = "a" * 1000
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, long_text)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": long_text}
        )
    
    def test_insert_text_empty_string(self):
        """Test insertion of empty string"""
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, "")
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": ""}
        )
    
    def test_insert_text_unicode(self):
        """Test insertion of unicode text"""
        unicode_text = "こんにちは世界"
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, unicode_text)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": unicode_text}
        )
    
    def test_insert_text_failure(self):
        """Test text insertion failure"""
        self.mock_driver.execute_cdp_cmd.side_effect = Exception("CDP error")
        
        with self.assertRaises(Exception) as context:
            insert_text(self.mock_driver, "test text")
        
        self.assertEqual(str(context.exception), "CDP error")
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": "test text"}
        )
    
    def test_insert_text_none_driver(self):
        """Test with None driver"""
        with self.assertRaises(AttributeError):
            insert_text(None, "test text")
    
    def test_insert_text_none_text(self):
        """Test with None text"""
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, None)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": None}
        )
    
    def test_insert_text_special_characters(self):
        """Test insertion of special characters"""
        special_text = "!@#$%^&*()_+-=[]{}|;:'\",.<>?/`~"
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, special_text)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": special_text}
        )
    
    def test_insert_text_newlines(self):
        """Test insertion of text with newlines"""
        multiline_text = "line1\nline2\nline3"
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, multiline_text)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": multiline_text}
        )
    
    def test_insert_text_tabs(self):
        """Test insertion of text with tabs"""
        tabbed_text = "column1\tcolumn2\tcolumn3"
        expected_result = {"success": True}
        self.mock_driver.execute_cdp_cmd.return_value = expected_result
        
        result = insert_text(self.mock_driver, tabbed_text)
        
        self.assertEqual(result, expected_result)
        self.mock_driver.execute_cdp_cmd.assert_called_once_with(
            "Input.insertText", {"text": tabbed_text}
        )


if __name__ == '__main__':
    unittest.main()
