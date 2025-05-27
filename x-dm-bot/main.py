#!/usr/bin/env python3
"""
X (Twitter) DM Bot with Selenium Automation
"""

import json
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class XDMBot:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the X DM Bot"""
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {config_path}")
            raise
    
    def _setup_driver(self):
        """Setup Chrome driver with options"""
        # 古いchromedriverをPATHから除外
        current_path = os.environ.get('PATH', '')
        path_dirs = current_path.split(':')
        # /usr/local/bin を除外
        filtered_dirs = [d for d in path_dirs if d != '/usr/local/bin']
        os.environ['PATH'] = ':'.join(filtered_dirs)
        
        options = uc.ChromeOptions()
        
        # Add Chrome options for better automation
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent
        options.add_argument(f'user-agent={self.config.get("user_agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")}')
        
        # Optional: Run in headless mode
        if self.config.get("headless", False):
            options.add_argument("--headless")
        
        # Initialize driver with undetected-chromedriver
        self.driver = uc.Chrome(options=options)
        
        # PATHを元に戻す
        os.environ['PATH'] = current_path
        self.wait = WebDriverWait(self.driver, 20)
        
        # Execute CDP commands to hide automation
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def login(self):
        """Login to X (Twitter)"""
        try:
            logger.info("Starting login process...")
            self.driver.get("https://twitter.com/login")
            
            # Wait for and enter username
            username_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]'))
            )
            username_input.send_keys(os.getenv("X_USERNAME"))
            username_input.send_keys(Keys.RETURN)
            
            time.sleep(2)
            
            # Handle potential username verification
            try:
                phone_input = self.driver.find_element(By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]')
                if phone_input:
                    logger.info("Phone/email verification required")
                    phone_input.send_keys(os.getenv("X_PHONE_OR_EMAIL"))
                    phone_input.send_keys(Keys.RETURN)
                    time.sleep(2)
            except NoSuchElementException:
                pass
            
            # Enter password
            password_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]'))
            )
            password_input.send_keys(os.getenv("X_PASSWORD"))
            password_input.send_keys(Keys.RETURN)
            
            # Wait for login to complete
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="primaryColumn"]'))
            )
            
            logger.info("Login successful!")
            time.sleep(3)
            
        except TimeoutException:
            logger.error("Login timeout - check your credentials")
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def navigate_to_messages(self):
        """Navigate to the messages section"""
        try:
            logger.info("Navigating to messages...")
            
            # Click on Messages link
            messages_link = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/messages"]'))
            )
            messages_link.click()
            
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to navigate to messages: {str(e)}")
            raise
    
    def search_user(self, username: str) -> bool:
        """Search for a user to send DM"""
        try:
            logger.info(f"Searching for user: {username}")
            
            # Click on new message button
            new_message_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="NewDM_Button"]'))
            )
            new_message_btn.click()
            
            time.sleep(1)
            
            # Search for user
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="searchPeople"]'))
            )
            search_input.send_keys(username)
            
            time.sleep(2)
            
            # Click on the first result
            user_result = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="typeaheadResult"]'))
            )
            user_result.click()
            
            # Click Next button
            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="nextButton"]'))
            )
            next_btn.click()
            
            return True
            
        except TimeoutException:
            logger.warning(f"User {username} not found or cannot be messaged")
            return False
        except Exception as e:
            logger.error(f"Error searching for user {username}: {str(e)}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send a DM message"""
        try:
            logger.info("Sending message...")
            
            # Find message input
            message_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="dmComposerTextInput"]'))
            )
            
            # Type message with human-like delays
            for char in message:
                message_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            # Send message
            send_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="dmComposerSendButton"]'))
            )
            send_btn.click()
            
            logger.info("Message sent successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def send_campaign_messages(self):
        """Send messages to all users in the campaign"""
        campaign = self.config.get("campaign", {})
        recipients = campaign.get("recipients", [])
        message_template = campaign.get("message_template", "")
        delay_range = campaign.get("delay_between_messages", [30, 60])
        
        if not recipients:
            logger.warning("No recipients found in campaign")
            return
        
        success_count = 0
        fail_count = 0
        
        for recipient in recipients:
            username = recipient.get("username")
            custom_message = message_template.format(
                name=recipient.get("name", "there"),
                custom_field=recipient.get("custom_field", "")
            )
            
            if self.search_user(username):
                if self.send_message(custom_message):
                    success_count += 1
                    logger.info(f"✓ Message sent to {username}")
                else:
                    fail_count += 1
                    logger.error(f"✗ Failed to send message to {username}")
            else:
                fail_count += 1
                logger.error(f"✗ Could not find user {username}")
            
            # Random delay between messages
            delay = random.randint(delay_range[0], delay_range[1])
            logger.info(f"Waiting {delay} seconds before next message...")
            time.sleep(delay)
        
        logger.info(f"Campaign complete! Success: {success_count}, Failed: {fail_count}")
    
    def run(self):
        """Main execution flow"""
        try:
            self._setup_driver()
            self.login()
            self.navigate_to_messages()
            self.send_campaign_messages()
            
        except Exception as e:
            logger.error(f"Bot execution failed: {str(e)}")
            raise
        finally:
            if self.driver:
                logger.info("Closing browser...")
                self.driver.quit()


def main():
    """Main entry point"""
    bot = XDMBot()
    bot.run()


if __name__ == "__main__":
    main()