"""
Tests for safe_click.py
"""
import unittest
from unittest.mock import patch, MagicMock
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from bot.utils.safe_click import safe_click, safe_click_by_selector


class TestSafeClick(unittest.TestCase):
    """Test safe click functions"""
    
    def setUp(self):
        self.mock_driver = MagicMock(spec=WebDriver)
        self.mock_element = MagicMock(spec=WebElement)
    
    @patch('bot.utils.safe_click.WebDriverWait')
    @patch('bot.utils.safe_click.time.sleep')
    def test_safe_click_success(self, mock_sleep, mock_wait):
        """Test successful element click"""
        mock_wait.return_value.until.return_value = self.mock_element
        
        result = safe_click(self.mock_driver, self.mock_element)
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
        self.mock_element.click.assert_called_once()
        mock_sleep.assert_not_called()
    
    @patch('bot.utils.safe_click.WebDriverWait')
    @patch('bot.utils.safe_click.time.sleep')
    def test_safe_click_retry_success(self, mock_sleep, mock_wait):
        """Test element click with retry success"""
        mock_element_returned = MagicMock()
        mock_wait.return_value.until.side_effect = [Exception("Not clickable"), mock_element_returned]
        
        result = safe_click(self.mock_driver, self.mock_element, max_retries=2)
        
        self.assertTrue(result)
        self.assertEqual(mock_wait.call_count, 2)
        mock_element_returned.click.assert_called_once()
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1
    
    @patch('bot.utils.safe_click.WebDriverWait')
    @patch('bot.utils.safe_click.time.sleep')
    def test_safe_click_all_retries_fail(self, mock_sleep, mock_wait):
        """Test element click with all retries failing"""
        mock_wait.return_value.until.side_effect = Exception("Not clickable")
        
        result = safe_click(self.mock_driver, self.mock_element, max_retries=3)
        
        self.assertFalse(result)
        self.assertEqual(mock_wait.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # One less than max_retries
        mock_sleep.assert_any_call(1)  # 2^0 = 1
        mock_sleep.assert_any_call(2)  # 2^1 = 2
    
    @patch('bot.utils.safe_click.WebDriverWait')
    def test_safe_click_by_selector_success(self, mock_wait):
        """Test successful selector click"""
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element
        
        result = safe_click_by_selector(self.mock_driver, "button.submit")
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
        from unittest.mock import ANY
        mock_wait.return_value.until.assert_called_once_with(ANY)
        mock_element.click.assert_called_once()
    
    @patch('bot.utils.safe_click.WebDriverWait')
    @patch('bot.utils.safe_click.time.sleep')
    def test_safe_click_by_selector_retry_success(self, mock_sleep, mock_wait):
        """Test selector click with retry success"""
        mock_element = MagicMock()
        mock_wait.return_value.until.side_effect = [Exception("Not found"), mock_element]
        
        result = safe_click_by_selector(self.mock_driver, "button.submit", max_retries=2)
        
        self.assertTrue(result)
        self.assertEqual(mock_wait.call_count, 2)
        mock_element.click.assert_called_once()
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1
    
    @patch('bot.utils.safe_click.WebDriverWait')
    @patch('bot.utils.safe_click.time.sleep')
    def test_safe_click_by_selector_all_retries_fail(self, mock_sleep, mock_wait):
        """Test selector click with all retries failing"""
        mock_wait.return_value.until.side_effect = Exception("Not found")
        
        result = safe_click_by_selector(self.mock_driver, "button.submit", max_retries=5)
        
        self.assertFalse(result)
        self.assertEqual(mock_wait.call_count, 5)
        self.assertEqual(mock_sleep.call_count, 4)  # One less than max_retries
        mock_sleep.assert_any_call(1)   # 2^0 = 1
        mock_sleep.assert_any_call(2)   # 2^1 = 2
        mock_sleep.assert_any_call(4)   # 2^2 = 4
        mock_sleep.assert_any_call(8)   # 2^3 = 8
    
    @patch('bot.utils.safe_click.WebDriverWait')
    def test_safe_click_by_selector_with_by_xpath(self, mock_wait):
        """Test selector click with XPath selector"""
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element
        
        result = safe_click_by_selector(
            self.mock_driver, 
            "//button[@class='submit']", 
            by=By.XPATH
        )
        
        self.assertTrue(result)
        mock_wait.assert_called_once_with(self.mock_driver, 10)
        from unittest.mock import ANY
        mock_wait.return_value.until.assert_called_once_with(ANY)
        mock_element.click.assert_called_once()


if __name__ == '__main__':
    unittest.main()
