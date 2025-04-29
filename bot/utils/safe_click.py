"""
Safe click utility with retry mechanism
"""
import time
import logging
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

def safe_click(driver: WebDriver, element: WebElement, timeout: int = 10, max_retries: int = 5) -> bool:
    """
    Safely click an element with retry mechanism
    
    Args:
        driver: WebDriver instance
        element: WebElement to click
        timeout: Timeout for waiting for element to be clickable
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if click was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable(element)
            )
            
            element.click()
            logger.info(f"Successfully clicked element on attempt {attempt + 1}")
            return True
            
        except Exception as e:
            logger.warning(f"Click attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to click element after {max_retries} attempts")
                return False
    
    return False

def safe_click_by_selector(driver: WebDriver, selector: str, by: By = By.CSS_SELECTOR, 
                          timeout: int = 10, max_retries: int = 5) -> bool:
    """
    Safely click an element by selector with retry mechanism
    
    Args:
        driver: WebDriver instance
        selector: Element selector
        by: Selector type (default: CSS_SELECTOR)
        timeout: Timeout for waiting for element to be clickable
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if click was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            elements = driver.find_elements(by, selector)
            if not elements:
                logger.warning(f"No elements found matching selector: {selector}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"No elements found matching selector after {max_retries} attempts")
                    return False
            
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                element.click()
                logger.info(f"Successfully clicked element by selector on attempt {attempt + 1} (approach 1)")
                return True
            except Exception as e1:
                logger.warning(f"Click approach 1 failed: {e1}")
                
                try:
                    logger.info("Trying JavaScript click...")
                    element = elements[0]
                    driver.execute_script("arguments[0].click();", element)
                    logger.info(f"Successfully clicked element by JavaScript on attempt {attempt + 1} (approach 2)")
                    return True
                except Exception as e2:
                    logger.warning(f"Click approach 2 failed: {e2}")
                    
                    try:
                        logger.info("Trying Actions chain click...")
                        from selenium.webdriver.common.action_chains import ActionChains
                        element = elements[0]
                        actions = ActionChains(driver)
                        actions.move_to_element(element).click().perform()
                        logger.info(f"Successfully clicked element by Actions chain on attempt {attempt + 1} (approach 3)")
                        return True
                    except Exception as e3:
                        logger.warning(f"Click approach 3 failed: {e3}")
                        
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.info(f"Waiting {wait_time} seconds before retry...")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Failed to click element by selector after {max_retries} attempts and 3 approaches")
                            return False
        
        except Exception as e:
            logger.warning(f"Click attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to click element by selector after {max_retries} attempts")
                return False
    
    return False
