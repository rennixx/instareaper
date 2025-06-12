#!/usr/bin/env python3
"""
Instagram Web Authentication Module

This module handles Instagram authentication through web browser for one-time setup.
Uses Selenium to automate the login process and extract session cookies.
"""

import os
import json
import time
import logging
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class InstagramWebAuth:
    """
    Handles Instagram authentication through web browser interface.
    """
    
    def __init__(self, session_file: str = "data/instagram_web_session.json"):
        """
        Initialize web authentication handler.
        
        Args:
            session_file: Path to save session data
        """
        self.session_file = session_file
        self.driver = None
        self.session_data = None
        
        # Setup logging
        self.setup_logging()
        
        self.logger.info("Instagram Web Auth initialized")
    
    def setup_logging(self):
        """Setup logging for web authentication"""
        try:
            # Ensure logs directory exists
            log_dir = "data/logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure logger
            self.logger = logging.getLogger('InstagramWebAuth')
            self.logger.setLevel(logging.INFO)
            
            # Remove existing handlers to avoid duplicates
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create file handler
            log_file = os.path.join(log_dir, 'instagram_web_auth.log')
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Error setting up web auth logging: {e}")
    
    def setup_driver(self) -> bool:
        """
        Setup Chrome WebDriver with appropriate options.
        
        Returns:
            bool: True if driver setup successful
        """
        try:
            self.logger.info("Setting up Chrome WebDriver...")
            
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Setup Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up WebDriver: {e}")
            return False
    
    def authenticate_web(self) -> Tuple[bool, str]:
        """
        Perform web-based Instagram authentication.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.setup_driver():
                return False, "Failed to setup web driver"
            
            self.logger.info("Starting Instagram web authentication...")
            
            # Navigate to Instagram login page
            self.driver.get("https://www.instagram.com/accounts/login/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            
            self.logger.info("Instagram login page loaded")
            
            # Display instructions to user
            print("\n🌐 Instagram Web Authentication")
            print("=" * 40)
            print("📱 A browser window has opened with Instagram login page")
            print("🔐 Please complete the following steps:")
            print("   1. Enter your Instagram username and password")
            print("   2. Complete any 2FA/verification if prompted")
            print("   3. Wait until you see your Instagram feed/home page")
            print("   4. Come back here and press ENTER when logged in")
            print("\n⚠️  Do NOT close the browser window!")
            print("⏳ Waiting for you to complete login...")
            
            # Wait for user to complete login
            input("\n✅ Press ENTER after you've successfully logged into Instagram: ")
            
            # Check if login was successful by looking for feed elements
            self.logger.info("Checking login status...")
            
            # Wait a bit for page to stabilize
            time.sleep(3)
            
            # Try to find elements that indicate successful login
            login_success = False
            success_indicators = [
                "//a[@href='/']",  # Home link
                "//svg[@aria-label='Home']",  # Home icon
                "//a[contains(@href, '/direct/')]",  # Messages link
                "//button[contains(text(), 'Share')]",  # Share button
                "//*[contains(@class, 'feed')]"  # Feed container
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element:
                        login_success = True
                        self.logger.info(f"Login success indicator found: {indicator}")
                        break
                except NoSuchElementException:
                    continue
            
            if not login_success:
                # Check current URL as backup
                current_url = self.driver.current_url
                if "instagram.com" in current_url and "login" not in current_url:
                    login_success = True
                    self.logger.info(f"Login success detected from URL: {current_url}")
            
            if login_success:
                # Extract session cookies
                self.logger.info("Extracting session cookies...")
                cookies = self.driver.get_cookies()
                
                # Save session data
                session_data = {
                    "cookies": cookies,
                    "user_agent": self.driver.execute_script("return navigator.userAgent;"),
                    "timestamp": time.time(),
                    "url": self.driver.current_url
                }
                
                # Ensure session directory exists
                os.makedirs(os.path.dirname(self.session_file), exist_ok=True)
                
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                self.session_data = session_data
                
                print("✅ Login successful! Session saved.")
                print(f"💾 Session data saved to: {self.session_file}")
                
                self.logger.info("Instagram web authentication successful")
                return True, "Web authentication successful"
            else:
                print("❌ Login not detected. Please try again.")
                self.logger.warning("Login not detected after user confirmation")
                return False, "Login not detected"
                
        except TimeoutException:
            error_msg = "Timeout waiting for Instagram page to load"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Web authentication error: {e}"
            self.logger.error(error_msg)
            return False, error_msg
        finally:
            self.cleanup()
    
    def load_session(self) -> bool:
        """
        Load existing session data.
        
        Returns:
            bool: True if session loaded successfully
        """
        try:
            if not os.path.exists(self.session_file):
                self.logger.info("No existing session file found")
                return False
            
            with open(self.session_file, 'r') as f:
                self.session_data = json.load(f)
            
            # Check if session is not too old (7 days)
            session_age = time.time() - self.session_data.get('timestamp', 0)
            if session_age > 7 * 24 * 3600:  # 7 days
                self.logger.info("Session too old, requiring re-authentication")
                return False
            
            self.logger.info("Session loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading session: {e}")
            return False
    
    def get_session_cookies(self) -> Optional[Dict]:
        """
        Get session cookies for use with instagrapi.
        
        Returns:
            Dict with session cookies or None
        """
        if not self.session_data:
            if not self.load_session():
                return None
        
        return self.session_data.get('cookies', [])
    
    def is_authenticated(self) -> bool:
        """
        Check if we have valid authentication.
        
        Returns:
            bool: True if authenticated
        """
        return self.session_data is not None or self.load_session()
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up WebDriver: {e}")
            finally:
                self.driver = None
    
    def clear_session(self):
        """Clear stored session data"""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                self.logger.info("Session file cleared")
            self.session_data = None
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")

def test_web_auth():
    """Test the web authentication system"""
    print("🧪 Testing Instagram Web Authentication")
    print("=" * 40)
    
    auth = InstagramWebAuth()
    
    # Check existing session
    if auth.is_authenticated():
        print("✅ Existing session found")
        cookies = auth.get_session_cookies()
        print(f"📊 Session has {len(cookies)} cookies")
        return True
    else:
        print("❌ No valid session found")
        print("🌐 Starting web authentication...")
        
        success, message = auth.authenticate_web()
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False

if __name__ == "__main__":
    test_web_auth() 