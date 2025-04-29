"""
Simple test script for safe_click functionality using standard Selenium WebDriver
"""
import os
import sys
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.utils.safe_click import safe_click_by_selector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_standard_driver():
    """Create a standard Selenium WebDriver"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        return driver
    except Exception as e:
        logger.error(f"Error creating standard WebDriver: {e}")
        return None

def test_safe_click():
    """Test the safe_click functionality"""
    try:
        logger.info("Creating standard WebDriver...")
        driver = create_standard_driver()
        
        if not driver:
            logger.error("Failed to create WebDriver")
            return False
        
        logger.info("Navigating to example.com...")
        driver.get("https://www.example.com")
        
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        logger.info("Testing safe_click_by_selector on a link...")
        result = safe_click_by_selector(driver, "a", timeout=10, max_retries=5)
        
        if result:
            logger.info("Successfully clicked link using safe_click_by_selector")
            
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            current_url = driver.current_url
            logger.info(f"Current URL after click: {current_url}")
            
            if "iana.org" in current_url.lower():
                logger.info("Navigation successful, test passed")
                driver.quit()
                return True
            else:
                logger.error(f"Navigation failed, unexpected URL: {current_url}")
                driver.quit()
                return False
        else:
            logger.error("Failed to click link using safe_click_by_selector")
            driver.quit()
            return False
    
    except Exception as e:
        logger.error(f"Error in test_safe_click: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def main():
    """Main function"""
    try:
        logger.info("Starting safe_click test...")
        
        result = test_safe_click()
        
        if result:
            logger.info("Test completed successfully")
            return 0
        else:
            logger.error("Test failed")
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
