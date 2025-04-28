"""
Chrome DevTools Protocol utilities for text input
"""
import logging
from typing import Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


def insert_text(driver: WebDriver, text: str) -> Dict[str, Any]:
    """
    Insert text using Chrome DevTools Protocol
    
    Args:
        driver: Selenium WebDriver instance
        text: Text to insert
        
    Returns:
        Dict[str, Any]: CDP command result
    """
    try:
        result = driver.execute_cdp_cmd("Input.insertText", {"text": text})
        if text is not None:
            logger.debug(f"CDP insertText successful: {text[:50]}...")
        else:
            logger.debug("CDP insertText successful: None")
        return result
    except Exception as e:
        logger.error(f"CDP insertText failed: {e}")
        raise
