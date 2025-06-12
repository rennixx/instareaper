#!/usr/bin/env python3
"""
Post Scheduler Module for InstaReaper

This module handles automated posting of videos from the local database to Instagram
at scheduled intervals. Includes configuration management, logging, and background threading.
"""

import os
import json
import time
import logging
import threading
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
import schedule

from data.database import DatabaseHandler
from uploader.instagram_poster import InstagramPoster


class PostScheduler:
    """
    Handles automated posting of videos to Instagram on a scheduled basis.
    """
    
    def __init__(self, database_handler: DatabaseHandler = None, 
                 instagram_poster: InstagramPoster = None,
                 config_path: str = "config/schedule.json"):
        """
        Initialize the post scheduler.
        
        Args:
            database_handler: Database handler for video operations
            instagram_poster: Instagram poster for uploading videos
            config_path: Path to scheduler configuration file
        """
        self.database_handler = database_handler or DatabaseHandler()
        self.instagram_poster = instagram_poster or InstagramPoster()
        self.config_path = config_path
        
        # Scheduler state
        self.is_running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        # Setup logging first
        self.setup_logging()
        
        # Configuration
        self.config = {}
        self.load_config()
        
        # Callbacks for GUI integration
        self.on_post_success: Optional[Callable] = None
        self.on_post_failure: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        
        self.logger.info("PostScheduler initialized")
    
    def setup_logging(self):
        """Setup logging for scheduler operations"""
        try:
            # Ensure logs directory exists
            log_dir = "data/logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure logger
            self.logger = logging.getLogger('PostScheduler')
            self.logger.setLevel(logging.INFO)
            
            # Remove existing handlers to avoid duplicates
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create file handler
            log_file = os.path.join(log_dir, 'scheduler.log')
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
            self.logger.info("Scheduler logging system initialized")
            
        except Exception as e:
            print(f"Error setting up scheduler logging: {e}")
    
    def load_config(self):
        """Load scheduler configuration from JSON file"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # Check if config file exists
            if not os.path.exists(self.config_path):
                self.logger.warning(f"Config file not found: {self.config_path}")
                self.create_default_config()
                return
            
            # Load configuration
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Validate required fields
            self.validate_config()
            self.logger.info("Scheduler configuration loaded successfully")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            self.create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create a default configuration file"""
        try:
            default_config = {
                "enabled": False,
                "posting": {
                    "frequency_minutes": 120,  # Post every 2 hours
                    "randomize_delay": True,   # Add random delay to appear more natural
                    "min_delay_minutes": 15,   # Minimum additional delay
                    "max_delay_minutes": 45,   # Maximum additional delay
                    "max_posts_per_day": 12,   # Maximum posts per 24 hours
                    "quiet_hours": {
                        "enabled": True,
                        "start_hour": 23,      # 11 PM
                        "end_hour": 7          # 7 AM
                    }
                },
                "content_selection": {
                    "sort_by": "created_at",   # Sort criteria: created_at, duration, subreddit
                    "sort_order": "asc",       # asc or desc
                    "filter_by_duration": True,
                    "max_duration_seconds": 60,
                    "exclude_subreddits": [],  # Subreddits to skip
                    "preferred_subreddits": [] # Prioritize these subreddits
                },
                "caption_settings": {
                    "use_original_title": True,
                    "add_source_credit": True,
                    "add_hashtags": True,
                    "default_hashtags": ["#viral", "#content", "#reddit", "#instareaper"],
                    "max_caption_length": 2000
                },
                "error_handling": {
                    "retry_failed_posts": True,
                    "max_retries": 3,
                    "retry_delay_minutes": 30,
                    "skip_on_consecutive_failures": 5
                },
                "notes": [
                    "enabled: Set to true to enable automatic posting",
                    "frequency_minutes: How often to check for new videos to post",
                    "randomize_delay: Adds random delay to posting to appear more natural",
                    "quiet_hours: Skip posting during these hours",
                    "max_posts_per_day: Prevents exceeding Instagram limits"
                ]
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            self.config = default_config
            self.logger.info(f"Created default config at: {self.config_path}")
            print(f"⚠️  Created default scheduler config at: {self.config_path}")
            print("Edit this file to configure automatic posting settings.")
            
        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")
            # Fallback minimal config
            self.config = {"enabled": False, "posting": {"frequency_minutes": 120}}
    
    def validate_config(self):
        """Validate configuration has required fields"""
        required_sections = ['posting']
        required_fields = {
            'posting': ['frequency_minutes']
        }
        
        for section in required_sections:
            if section not in self.config:
                self.logger.warning(f"Missing config section: {section}")
                self.config[section] = {}
        
        for section, fields in required_fields.items():
            for field in fields:
                if field not in self.config[section]:
                    self.logger.warning(f"Missing config field: {section}.{field}")
                    # Set default values
                    if field == 'frequency_minutes':
                        self.config[section][field] = 120
    
    def is_enabled(self) -> bool:
        """Check if scheduler is enabled in configuration"""
        return self.config.get('enabled', False)
    
    def is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        try:
            quiet_config = self.config.get('posting', {}).get('quiet_hours', {})
            if not quiet_config.get('enabled', False):
                return False
            
            current_hour = datetime.now().hour
            start_hour = quiet_config.get('start_hour', 23)
            end_hour = quiet_config.get('end_hour', 7)
            
            if start_hour <= end_hour:
                # Same day range (e.g., 9 AM to 5 PM)
                return start_hour <= current_hour <= end_hour
            else:
                # Overnight range (e.g., 11 PM to 7 AM)
                return current_hour >= start_hour or current_hour <= end_hour
                
        except Exception as e:
            self.logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def get_posts_today(self) -> int:
        """Get number of posts made today"""
        try:
            today = datetime.now().date()
            # This would need to be implemented in the database
            # For now, return 0 as a placeholder
            return 0
        except Exception as e:
            self.logger.error(f"Error getting today's post count: {e}")
            return 0
    
    def select_next_video(self) -> Optional[Dict]:
        """Select the next video to post based on configuration"""
        try:
            # Get all unposted videos
            all_videos = self.database_handler.get_all_videos()
            unposted_videos = [v for v in all_videos if not v.get('posted_to_instagram', False)]
            
            if not unposted_videos:
                self.logger.info("No unposted videos available")
                return None
            
            # Filter by duration if enabled
            content_config = self.config.get('content_selection', {})
            if content_config.get('filter_by_duration', True):
                max_duration = content_config.get('max_duration_seconds', 60)
                unposted_videos = [v for v in unposted_videos 
                                 if v.get('duration', 0) <= max_duration]
            
            if not unposted_videos:
                self.logger.info("No videos meeting duration criteria")
                return None
            
            # Filter by excluded subreddits
            excluded_subs = content_config.get('exclude_subreddits', [])
            if excluded_subs:
                unposted_videos = [v for v in unposted_videos 
                                 if v.get('subreddit', '') not in excluded_subs]
            
            # Prioritize preferred subreddits
            preferred_subs = content_config.get('preferred_subreddits', [])
            if preferred_subs:
                preferred_videos = [v for v in unposted_videos 
                                  if v.get('subreddit', '') in preferred_subs]
                if preferred_videos:
                    unposted_videos = preferred_videos
            
            if not unposted_videos:
                self.logger.info("No videos after filtering")
                return None
            
            # Sort videos based on configuration
            sort_by = content_config.get('sort_by', 'created_at')
            sort_order = content_config.get('sort_order', 'asc')
            
            if sort_by == 'duration':
                unposted_videos.sort(key=lambda x: x.get('duration', 0), 
                                   reverse=(sort_order == 'desc'))
            elif sort_by == 'subreddit':
                unposted_videos.sort(key=lambda x: x.get('subreddit', ''), 
                                   reverse=(sort_order == 'desc'))
            else:  # created_at or default
                unposted_videos.sort(key=lambda x: x.get('created_at', ''), 
                                   reverse=(sort_order == 'desc'))
            
            selected_video = unposted_videos[0]
            self.logger.info(f"Selected video for posting: {selected_video.get('title', 'Unknown')}")
            return selected_video
            
        except Exception as e:
            self.logger.error(f"Error selecting next video: {e}")
            return None
    
    def generate_caption(self, video_data: Dict) -> str:
        """Generate caption for video based on configuration"""
        try:
            caption_config = self.config.get('caption_settings', {})
            
            caption_parts = []
            
            # Add title if enabled
            if caption_config.get('use_original_title', True):
                title = video_data.get('title', '')
                if title:
                    caption_parts.append(title)
            
            # Add source credit if enabled
            if caption_config.get('add_source_credit', True):
                subreddit = video_data.get('subreddit', '')
                if subreddit:
                    caption_parts.append(f"\nSource: r/{subreddit}")
            
            # Add duration info
            duration = video_data.get('duration', 0)
            if duration > 0:
                caption_parts.append(f"Duration: {duration:.1f}s")
            
            # Add hashtags if enabled
            if caption_config.get('add_hashtags', True):
                hashtags = caption_config.get('default_hashtags', [])
                if hashtags:
                    caption_parts.append("\n" + " ".join(hashtags))
            
            # Combine and limit length
            caption = "\n".join(caption_parts)
            max_length = caption_config.get('max_caption_length', 2000)
            
            if len(caption) > max_length:
                # Truncate and add ellipsis
                caption = caption[:max_length-3] + "..."
            
            return caption
            
        except Exception as e:
            self.logger.error(f"Error generating caption: {e}")
            return "Great content! #viral #content"
    
    def post_video(self, video_data: Dict) -> bool:
        """Post a single video to Instagram"""
        try:
            video_title = video_data.get('title', 'Unknown Video')
            self.logger.info(f"Attempting to post video: {video_title}")
            
            # Get video file path
            video_path = video_data.get('filepath', '')
            if not video_path:
                filename = video_data.get('filename', '')
                if filename:
                    video_path = os.path.join('data/videos', filename)
            
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return False
            
            # Generate caption
            caption = self.generate_caption(video_data)
            
            # Post to Instagram
            result = self.instagram_poster.upload_video(video_path, caption)
            
            if result['success']:
                # Update database with posted status
                video_data['posted_to_instagram'] = True
                video_data['instagram_post_id'] = result['post_id']
                video_data['instagram_posted_at'] = datetime.now().isoformat()
                
                self.logger.info(f"Successfully posted video: {video_title} (ID: {result['post_id']})")
                
                # Call success callback
                if self.on_post_success:
                    self.on_post_success(video_data, result)
                
                return True
            else:
                self.logger.error(f"Failed to post video: {video_title} - {result['message']}")
                
                # Call failure callback
                if self.on_post_failure:
                    self.on_post_failure(video_data, result)
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error posting video: {e}")
            return False
    
    def scheduler_loop(self):
        """Main scheduler loop that runs in a background thread"""
        self.logger.info("Scheduler loop started")
        
        while not self.stop_event.is_set():
            try:
                # Check if scheduler is enabled
                if not self.is_enabled():
                    self.logger.info("Scheduler disabled, sleeping...")
                    time.sleep(60)  # Check every minute if enabled
                    continue
                
                # Check quiet hours
                if self.is_quiet_hours():
                    self.logger.info("Currently in quiet hours, skipping post")
                    time.sleep(3600)  # Sleep for 1 hour
                    continue
                
                # Check daily post limit
                posts_today = self.get_posts_today()
                max_posts = self.config.get('posting', {}).get('max_posts_per_day', 12)
                if posts_today >= max_posts:
                    self.logger.info(f"Daily post limit reached ({posts_today}/{max_posts})")
                    # Sleep until tomorrow
                    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    sleep_seconds = (tomorrow - datetime.now()).total_seconds()
                    self.logger.info(f"Sleeping until tomorrow ({sleep_seconds/3600:.1f} hours)")
                    self.stop_event.wait(min(sleep_seconds, 3600))  # Max 1 hour sleep
                    continue
                
                # Select next video
                video_to_post = self.select_next_video()
                if not video_to_post:
                    self.logger.info("No videos available for posting")
                    time.sleep(1800)  # Sleep for 30 minutes
                    continue
                
                # Add randomized delay if enabled
                posting_config = self.config.get('posting', {})
                if posting_config.get('randomize_delay', True):
                    min_delay = posting_config.get('min_delay_minutes', 15)
                    max_delay = posting_config.get('max_delay_minutes', 45)
                    delay_minutes = random.randint(min_delay, max_delay)
                    self.logger.info(f"Adding random delay: {delay_minutes} minutes")
                    if self.stop_event.wait(delay_minutes * 60):
                        break  # Stop event was set
                
                # Post the video
                success = self.post_video(video_to_post)
                
                # Calculate next posting time
                frequency_minutes = posting_config.get('frequency_minutes', 120)
                next_post_time = datetime.now() + timedelta(minutes=frequency_minutes)
                self.logger.info(f"Next posting scheduled for: {next_post_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wait for next posting time
                if self.stop_event.wait(frequency_minutes * 60):
                    break  # Stop event was set
                
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")
                time.sleep(300)  # Sleep for 5 minutes on error
        
        self.logger.info("Scheduler loop stopped")
    
    def start(self):
        """Start the scheduler in a background thread"""
        try:
            if self.is_running:
                self.logger.warning("Scheduler is already running")
                return False
            
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(target=self.scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            self.is_running = True
            
            self.logger.info("Scheduler started successfully")
            if self.on_status_change:
                self.on_status_change(True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler cleanly"""
        try:
            if not self.is_running:
                self.logger.warning("Scheduler is not running")
                return False
            
            self.stop_event.set()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)  # Wait up to 5 seconds
            
            self.is_running = False
            self.logger.info("Scheduler stopped successfully")
            
            if self.on_status_change:
                self.on_status_change(False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        try:
            next_video = self.select_next_video()
            
            status = {
                'running': self.is_running,
                'enabled': self.is_enabled(),
                'quiet_hours': self.is_quiet_hours(),
                'posts_today': self.get_posts_today(),
                'max_posts_per_day': self.config.get('posting', {}).get('max_posts_per_day', 12),
                'frequency_minutes': self.config.get('posting', {}).get('frequency_minutes', 120),
                'next_video_available': next_video is not None,
                'next_video_title': next_video.get('title', 'None') if next_video else 'None'
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'running': False, 'enabled': False, 'error': str(e)}
    
    def set_callbacks(self, on_success: Callable = None, 
                     on_failure: Callable = None, 
                     on_status_change: Callable = None):
        """Set callback functions for GUI integration"""
        self.on_post_success = on_success
        self.on_post_failure = on_failure
        self.on_status_change = on_status_change


# Example usage and testing
if __name__ == "__main__":
    # Test the scheduler
    print("=== PostScheduler Test ===")
    
    try:
        # Initialize scheduler
        scheduler = PostScheduler()
        print("✓ PostScheduler initialized")
        
        # Check configuration
        print(f"✓ Configuration loaded: {scheduler.config_path}")
        print(f"   Enabled: {scheduler.is_enabled()}")
        print(f"   Frequency: {scheduler.config.get('posting', {}).get('frequency_minutes', 'N/A')} minutes")
        
        # Test video selection
        next_video = scheduler.select_next_video()
        if next_video:
            print(f"✓ Next video found: {next_video.get('title', 'Unknown')}")
        else:
            print("⚠️  No videos available for posting")
        
        # Test status
        status = scheduler.get_status()
        print(f"✓ Status retrieved: {status}")
        
        print("\n✅ All scheduler tests passed!")
        print("Use scheduler.start() to begin automatic posting")
        
    except Exception as e:
        print(f"❌ Test failed: {e}") 