#!/usr/bin/env python3
"""
Instagram Poster Module for InstaReaper

This module handles automated posting of videos to Instagram using instagrapi.
Includes secure credential management, rate limiting, and comprehensive logging.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Tuple, Optional
import cv2
import random

LOGGER = logging.getLogger(__name__)

try:
    from .instagram_web_auth import InstagramWebAuth
except ImportError:
    try:
        from uploader.instagram_web_auth import InstagramWebAuth
    except ImportError:
        InstagramWebAuth = None

try:
    from instagrapi import Client
    from instagrapi.exceptions import (
        LoginRequired, ChallengeRequired, 
        FeedbackRequired, PleaseWaitFewMinutes,
        ClientError
    )
    INSTAGRAPI_AVAILABLE = True
except ImportError as e:
    LOGGER.warning("instagrapi not available: %s", e)
    Client = None
    INSTAGRAPI_AVAILABLE = False


class InstagramPoster:
    """
    Handles Instagram video posting with secure authentication and rate limiting.
    """
    
    def __init__(self, config_path: str = "config/credentials.json"):
        """
        Initialize Instagram poster with credential path.
        
        Args:
            config_path: Path to credentials JSON file
        """
        self.config_path = config_path
        self.client = None
        self.credentials = None
        self.last_upload_time = None
        self.min_upload_interval = 1800  # 30 minutes in seconds (more conservative)
        self.max_upload_interval = 3600  # 1 hour in seconds
        self.daily_upload_limit = 3  # Max 3 posts per day
        self.upload_count_today = 0
        self.last_upload_date = None
        
        # Web authentication handler
        self.web_auth = InstagramWebAuth() if InstagramWebAuth else None
        
        # Setup logging
        self.setup_logging()
        
        # Load credentials
        self.load_credentials()
        
        self.logger.info("InstagramPoster initialized")
    
    def setup_logging(self):
        """Setup logging for Instagram operations"""
        try:
            # Ensure logs directory exists
            log_dir = "data/logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure logger
            self.logger = logging.getLogger('InstagramPoster')
            self.logger.setLevel(logging.INFO)
            
            # Remove existing handlers to avoid duplicates
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create file handler
            log_file = os.path.join(log_dir, 'instagram.log')
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
            self.logger.info("Instagram logging system initialized")
            
        except Exception as e:
            print(f"Error setting up Instagram logging: {e}")
    
    def load_credentials(self) -> bool:
        """
        Load Instagram credentials from secure JSON file.
        
        Returns:
            bool: True if credentials loaded successfully
        """
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Check if credentials file exists
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Credentials file not found: {self.config_path}")
                self.create_credentials_template()
                return False
            
            # Load credentials
            with open(self.config_path, 'r') as f:
                self.credentials = json.load(f)
            
            # Validate required fields
            required_fields = ['username', 'password']
            for field in required_fields:
                if field not in self.credentials:
                    self.logger.error(f"Missing required field in credentials: {field}")
                    return False
            
            self.logger.info("Instagram credentials loaded successfully")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in credentials file: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error loading credentials: {e}")
            return False
    
    def create_credentials_template(self):
        """Create a template credentials file for user to fill in"""
        try:
            template = {
                "username": "your_instagram_username",
                "password": "your_instagram_password",
                "session_file": "data/instagram_session.json",
                "device_settings": {
                    "device_id": "",
                    "uuid": "",
                    "phone_id": "",
                    "advertising_id": ""
                },
                "notes": [
                    "Replace 'your_instagram_username' and 'your_instagram_password' with your actual credentials",
                    "Keep this file secure and never commit it to version control",
                    "Device settings will be auto-generated on first login"
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(template, f, indent=4)
            
            self.logger.info(f"Created credentials template at: {self.config_path}")
            print(f"⚠️  Created credentials template at: {self.config_path}")
            print("Please edit this file with your Instagram credentials before using the poster.")
            
        except Exception as e:
            self.logger.error(f"Error creating credentials template: {e}")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Instagram using web authentication or stored credentials.
        
        Returns:
            bool: True if authentication successful
        """
        if not INSTAGRAPI_AVAILABLE or not Client:
            self.logger.error("instagrapi not available. Please install: pip install instagrapi")
            return False
        
        # Try to load existing session first
        if self.load_existing_session():
            return True
        
        # Try web authentication
        if self.web_auth and self.web_auth.is_authenticated():
            if self.authenticate_with_web_session():
                return True
        
        # Fallback to traditional authentication
        return self.authenticate_traditional()
    
    def load_existing_session(self) -> bool:
        """
        Load existing Instagram session if available.
        
        Returns:
            bool: True if session loaded successfully
        """
        try:
            session_file = "data/instagram_session.json"
            if not os.path.exists(session_file):
                return False
            
            self.logger.info("Loading existing Instagram session...")
            self.client = Client()
            self.client.load_settings(session_file)
            
            # Verify session is still valid
            try:
                user_info = self.client.account_info()
                self.logger.info(f"Existing session loaded successfully: @{user_info.username}")
                return True
            except Exception as e:
                self.logger.warning(f"Existing session invalid: {e}")
                # Delete invalid session file
                try:
                    os.remove(session_file)
                    self.logger.info("Removed invalid session file")
                except:
                    pass
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading existing session: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """
        Check if the client is currently authenticated.
        
        Returns:
            bool: True if authenticated
        """
        if not self.client:
            return False
        
        try:
            # Try to get account info to verify authentication
            self.client.account_info()
            return True
        except Exception:
            return False
    
    def authenticate_with_web_session(self) -> bool:
        """
        Authenticate using web session cookies.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Attempting web session authentication...")
            
            # Initialize client
            self.client = Client()
            
            # Get session cookies from web auth
            cookies = self.web_auth.get_session_cookies()
            if not cookies:
                self.logger.warning("No web session cookies available")
                return False
            
            self.logger.info(f"Found {len(cookies)} cookies from web session")
            
            # Create a settings dict for instagrapi
            settings = {
                "uuids": {
                    "phone_id": "",
                    "uuid": "",
                    "client_session_id": "",
                    "advertising_id": "",
                    "device_id": ""
                },
                "cookies": {},
                "last_login": time.time(),
                                 "device_settings": {
                     "cpu": "h2",
                     "dpi": "480dpi", 
                     "model": "SM-G988B",
                     "device": "x1s",
                     "resolution": "1440x3200",
                     "app_version": "275.0.0.27.98",
                     "manufacturer": "samsung",
                     "version_code": "423304410",
                     "android_release": "12",
                     "android_version": 31
                 },
                 "user_agent": "Instagram 275.0.0.27.98 Android (31/12; 480dpi; 1440x3200; samsung; SM-G988B; x1s; exynos990; en_US; 423304410)"
            }
            
            # Convert web cookies to instagrapi format
            for cookie in cookies:
                if cookie['name'] in ['sessionid', 'csrftoken', 'ds_user_id', 'rur']:
                    settings["cookies"][cookie['name']] = cookie['value']
                    self.logger.info(f"Added cookie: {cookie['name']}")
            
            # Load settings into client
            try:
                self.client.set_settings(settings)
                self.logger.info("Settings loaded into client")
                
                # Try to get account info to verify authentication
                user_info = self.client.account_info()
                self.logger.info(f"Web authentication successful: @{user_info.username}")
                
                # Save the session for future use
                session_file = "data/instagram_session.json"
                try:
                    os.makedirs(os.path.dirname(session_file), exist_ok=True)
                    self.client.dump_settings(session_file)
                    self.logger.info("Web session saved to instagrapi format")
                except Exception as e:
                    self.logger.warning(f"Failed to save session: {e}")
                
                return True
                
            except Exception as e:
                self.logger.warning(f"Web session verification failed: {e}")
                
                # Try alternative approach - direct cookie setting
                self.logger.info("Trying alternative cookie approach...")
                return self.authenticate_with_direct_cookies(cookies)
                
        except Exception as e:
            self.logger.error(f"Web session authentication failed: {e}")
            return False
    
    def authenticate_with_direct_cookies(self, cookies) -> bool:
        """
        Alternative method to authenticate with direct cookie setting.
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Reset client
            self.client = Client()
            
            # Convert cookies to requests session format
            import requests
            session = requests.Session()
            
            # Set cookies in session
            for cookie in cookies:
                session.cookies.set(
                    name=cookie['name'],
                    value=cookie['value'],
                    domain=cookie.get('domain', '.instagram.com'),
                    path=cookie.get('path', '/')
                )
            
            # Set the session in the client's private session
            self.client.private.session = session
            
            # Set required headers with more realistic values
            self.client.private.session.headers.update({
                'User-Agent': 'Instagram 275.0.0.27.98 Android (31/12; 480dpi; 1440x3200; samsung; SM-G988B; x1s; exynos990; en_US; 423304410)',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': next((c['value'] for c in cookies if c['name'] == 'csrftoken'), ''),
                'X-Instagram-AJAX': '1',
                'X-IG-App-ID': '936619743392459',
                'X-IG-WWW-Claim': '0',
                'Origin': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/',
            })
            
            # Try to get account info
            user_info = self.client.account_info()
            self.logger.info(f"Direct cookie authentication successful: @{user_info.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Direct cookie authentication failed: {e}")
            return False
    
    def authenticate_traditional(self) -> bool:
        """
        Traditional authentication with username/password.
        
        Returns:
            bool: True if authentication successful
        """
        if not self.credentials:
            self.logger.error("No credentials loaded")
            return False
        
        try:
            # Initialize client
            self.client = Client()
            
            # Try to load existing session
            session_file = self.credentials.get('session_file', 'data/instagram_session.json')
            if os.path.exists(session_file):
                try:
                    self.client.load_settings(session_file)
                    self.client.login(self.credentials['username'], self.credentials['password'])
                    self.logger.info("Loaded existing Instagram session")
                except Exception as e:
                    self.logger.warning(f"Failed to load session, logging in fresh: {e}")
                    self.client = Client()  # Reset client
            
            # Fresh login if session loading failed or no session exists
            if not hasattr(self.client, 'user_id') or not self.client.user_id:
                self.logger.info("Performing fresh Instagram login")
                self.client.login(self.credentials['username'], self.credentials['password'])
                
                # Save session for future use
                try:
                    os.makedirs(os.path.dirname(session_file), exist_ok=True)
                    self.client.dump_settings(session_file)
                    self.logger.info("Instagram session saved")
                except Exception as e:
                    self.logger.warning(f"Failed to save session: {e}")
            
            # Verify login
            user_info = self.client.account_info()
            self.logger.info(f"Successfully authenticated as: @{user_info.username}")
            return True
            
        except LoginRequired:
            self.logger.error("Instagram login required - credentials may be invalid")
            return False
        except ChallengeRequired as e:
            self.logger.error(f"Instagram challenge required: {e}")
            return False
        except PleaseWaitFewMinutes:
            self.logger.error("Instagram rate limit hit - please wait a few minutes")
            return False
        except Exception as e:
            self.logger.error(f"Instagram authentication failed: {e}")
            return False
    
    def setup_web_authentication(self) -> Tuple[bool, str]:
        """
        Setup web-based authentication (one-time).
        
        Returns:
            Tuple of (success, message)
        """
        if not self.web_auth:
            return False, "Web authentication not available"
        
        try:
            self.logger.info("Starting web authentication setup...")
            success, message = self.web_auth.authenticate_web()
            
            if success:
                self.logger.info("Web authentication setup successful")
                return True, "Web authentication configured successfully"
            else:
                self.logger.error(f"Web authentication setup failed: {message}")
                return False, f"Web authentication failed: {message}"
                
        except Exception as e:
            error_msg = f"Error setting up web authentication: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def check_video_duration(self, filepath: str) -> Tuple[bool, float]:
        """
        Check if video is under 60 seconds (Instagram requirement).
        
        Args:
            filepath: Path to video file
            
        Returns:
            Tuple of (is_valid, duration_seconds)
        """
        try:
            cap = cv2.VideoCapture(filepath)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            
            if fps > 0:
                duration = frame_count / fps
            else:
                self.logger.warning(f"Could not determine FPS for video: {filepath}")
                return False, 0
            
            is_valid = duration <= 60.0
            if not is_valid:
                self.logger.warning(f"Video duration {duration:.1f}s exceeds Instagram 60s limit")
            
            return is_valid, duration
            
        except Exception as e:
            self.logger.error(f"Error checking video duration: {e}")
            return False, 0
    
    def check_rate_limit(self) -> Tuple[bool, int]:
        """
        Check if enough time has passed since last upload and daily limits.
        
        Returns:
            Tuple of (can_upload, seconds_to_wait)
        """
        current_time = time.time()
        current_date = date.today()
        
        # Check daily upload limit
        if self.last_upload_date != current_date:
            # Reset daily counter for new day
            self.upload_count_today = 0
            self.last_upload_date = current_date
        
        if self.upload_count_today >= self.daily_upload_limit:
            # Calculate seconds until midnight (next day)
            tomorrow = datetime.combine(current_date, datetime.min.time()) + timedelta(days=1)
            seconds_until_tomorrow = int((tomorrow - datetime.now()).total_seconds())
            return False, seconds_until_tomorrow
        
        # Check time-based rate limit
        if not self.last_upload_time:
            return True, 0
        
        time_since_last = current_time - self.last_upload_time
        
        if time_since_last >= self.min_upload_interval:
            return True, 0
        else:
            wait_time = int(self.min_upload_interval - time_since_last)
            return False, wait_time
    
    def upload_video(self, filepath: str, caption: str) -> Dict[str, any]:
        """
        Upload video to Instagram as a reel.
        
        Args:
            filepath: Path to video file
            caption: Caption for the post
            
        Returns:
            Dict with status, post_id, and message
        """
        result = {
            'success': False,
            'post_id': None,
            'message': '',
            'duration': 0
        }
        
        try:
            # Validate inputs
            if not os.path.exists(filepath):
                result['message'] = f"Video file not found: {filepath}"
                self.logger.error(result['message'])
                return result
            
            if not caption or len(caption.strip()) == 0:
                result['message'] = "Caption cannot be empty"
                self.logger.error(result['message'])
                return result
            
            # Check rate limiting
            can_upload, wait_time = self.check_rate_limit()
            if not can_upload:
                result['message'] = f"Rate limit: Please wait {wait_time} seconds before next upload"
                self.logger.warning(result['message'])
                return result
            
            # Check video duration
            is_valid_duration, duration = self.check_video_duration(filepath)
            result['duration'] = duration
            
            if not is_valid_duration:
                result['message'] = f"Video duration {duration:.1f}s exceeds Instagram 60s limit"
                self.logger.error(result['message'])
                return result
            
            # Ensure we have an authenticated client
            if not self.client or not self.is_authenticated():
                self.logger.info("Re-authenticating before upload...")
                if not self.authenticate():
                    result['message'] = "Failed to authenticate with Instagram"
                    self.logger.error(result['message'])
                    return result
            
            # Upload video
            self.logger.info(f"Starting Instagram upload: {os.path.basename(filepath)}")
            self.logger.info(f"Caption: {caption[:100]}{'...' if len(caption) > 100 else ''}")
            
            # Add human-like delay before upload (2-8 seconds)
            delay = random.uniform(2, 8)
            self.logger.info(f"Adding human-like delay: {delay:.1f}s")
            time.sleep(delay)
            
            # Use clip upload for reels
            media = self.client.clip_upload(
                path=filepath,
                caption=caption
            )
            
            # Update rate limiting and daily counter
            self.last_upload_time = time.time()
            self.upload_count_today += 1
            
            # Add another small delay after upload
            post_delay = random.uniform(1, 3)
            time.sleep(post_delay)
            
            # Success
            result['success'] = True
            result['post_id'] = media.id
            result['message'] = f"Successfully uploaded video as reel (ID: {media.id})"
            
            self.logger.info(f"Upload successful - Post ID: {media.id}")
            self.logger.info(f"Video duration: {duration:.1f}s")
            self.logger.info(f"Daily uploads: {self.upload_count_today}/{self.daily_upload_limit}")
            
            return result
            
        except FeedbackRequired as e:
            result['message'] = f"Instagram feedback required: {e}"
            self.logger.error(result['message'])
            return result
        except PleaseWaitFewMinutes:
            result['message'] = "Instagram rate limit hit - please wait before retrying"
            self.logger.error(result['message'])
            return result
        except Exception as e:
            result['message'] = f"Upload failed: {str(e)}"
            self.logger.error(f"Instagram upload error: {e}")
            return result
    
    def get_upload_stats(self) -> Dict[str, any]:
        """
        Get statistics about uploads.
        
        Returns:
            Dict with upload statistics
        """
        stats = {
            'last_upload_time': self.last_upload_time,
            'can_upload_now': self.check_rate_limit()[0],
            'seconds_until_next_upload': self.check_rate_limit()[1],
            'authenticated': self.client is not None
        }
        
        if self.last_upload_time:
            stats['last_upload_formatted'] = datetime.fromtimestamp(
                self.last_upload_time
            ).strftime('%Y-%m-%d %H:%M:%S')
        
        return stats
    
    def logout(self):
        """Safely logout from Instagram"""
        try:
            if self.client:
                self.client.logout()
                self.client = None
                self.logger.info("Logged out from Instagram")
        except Exception as e:
            self.logger.error(f"Error during logout: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test the Instagram poster
    poster = InstagramPoster()
    
    print("=== Instagram Poster Test ===")
    
    # Check if credentials are set up
    if not poster.credentials or poster.credentials.get('username') == 'your_instagram_username':
        print("❌ Please set up your credentials in config/credentials.json first")
        exit(1)
    
    # Test authentication
    if poster.authenticate():
        print("✅ Authentication successful")
        
        # Get stats
        stats = poster.get_upload_stats()
        print(f"📊 Upload stats: {stats}")
        
        # Test video duration check (using a test file if it exists)
        test_video = "data/videos/test.mp4"
        if os.path.exists(test_video):
            is_valid, duration = poster.check_video_duration(test_video)
            print(f"📹 Test video duration: {duration:.1f}s (Valid: {is_valid})")
        
        poster.logout()
    else:
        print("❌ Authentication failed") 
