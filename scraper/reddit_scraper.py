import requests
import os
import re
import time
import yaml
import logging
import yt_dlp
from datetime import datetime
from urllib.parse import urlparse
from processor.validate import VideoProcessor
from data.database import DatabaseHandler

class RedditScraper:
    def __init__(self):
        self.load_config()
        self.video_processor = VideoProcessor()
        self.setup_logging()
        self.db_handler = DatabaseHandler()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Default config
            self.config = {
                'reddit': {
                    'user_agent': 'InstaReaper/1.0',
                    'rate_limit': 1.0,
                    'max_video_duration': 60
                },
                'paths': {
                    'videos': 'data/videos',
                    'thumbnails': 'data/thumbnails',
                    'logs': 'data/logs'
                }
            }
    
    def setup_logging(self):
        """Setup logging for scraper operations"""
        log_dir = self.config['paths']['logs']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = os.path.join(log_dir, 'scraper.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'
        )
        self.logger = logging.getLogger(__name__)
        
    def is_repost(self, filename):
        """Check if video was already downloaded by checking database"""
        try:
            return self.db_handler.is_duplicate(filename)
        except Exception as e:
            self.logger.error(f"Error checking for repost: {e}")
            return False
    
    def has_watermark(self, title, filename):
        """Check for watermarks in title or filename"""
        watermark_indicators = [
            'tiktok', '@', 'watermark', 'logo', 'instagram', 'ig',
            'facebook', 'twitter', 'youtube', 'yt', 'snapchat',
            'made with', 'created with', 'powered by'
        ]
        
        text_to_check = f"{title.lower()} {filename.lower()}"
        return any(indicator in text_to_check for indicator in watermark_indicators)
    
    def log_video_metadata(self, video_metadata):
        """Store video metadata in database after successful download"""
        try:
            success = self.db_handler.add_video(video_metadata)
            if success:
                self.logger.info(f"Video metadata logged: {video_metadata['filename']}")
            return success
        except Exception as e:
            self.logger.error(f"Error logging video metadata: {e}")
            return False
            
    def scrape(self, subreddit: str, limit: int):
        """
        Scrape videos from specified subreddit
        
        Args:
            subreddit (str): Name of subreddit to scrape (e.g., 'memes', 'funny')
            limit (int): Maximum number of videos to scrape
            
        Returns:
            list: List of valid video metadata dictionaries
        """
        videos = []
        
        try:
            self.logger.info(f"Starting scrape of r/{subreddit} with limit {limit}")
            
            # Use requests to get Reddit JSON data (public API)
            headers = {
                'User-Agent': self.config['reddit']['user_agent']
            }
            
            # Get top posts from subreddit
            url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={limit * 3}&t=day"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            posts = data['data']['children']
            
            processed_count = 0
            
            for post_data in posts:
                if processed_count >= limit:
                    break
                    
                try:
                    post = post_data['data']
                    
                    # Check if post contains video
                    video_info = self.extract_video_info(post)
                    
                    if video_info:
                        # Generate filename
                        safe_title = re.sub(r'[^\w\-_\. ]', '_', post['title'])[:50]
                        timestamp = int(time.time())
                        filename = f"{timestamp}_{safe_title}.mp4"
                        
                        # Check for reposts
                        if self.is_repost(filename):
                            self.logger.info(f"Skipping repost: {filename}")
                            continue
                        
                        # Check for watermarks
                        if self.has_watermark(post['title'], filename):
                            self.logger.info(f"Skipping video with watermark: {post['title']}")
                            continue
                        
                        # Download and validate video
                        video_metadata = self.download_and_validate_video(video_info, post, filename)
                        
                        if video_metadata:
                            # Log to database
                            if self.log_video_metadata(video_metadata):
                                videos.append(video_metadata)
                                processed_count += 1
                                self.logger.info(f"Successfully processed: {video_metadata['title'][:30]}...")
                            
                        # Rate limiting
                        time.sleep(self.config['reddit']['rate_limit'])
                        
                except Exception as e:
                    self.logger.error(f"Error processing individual post: {e}")
                    continue
                        
        except Exception as e:
            self.logger.error(f"Error scraping r/{subreddit}: {e}")
            
        self.logger.info(f"Scraping completed. Found {len(videos)} valid videos from r/{subreddit}")
        return videos
    
    def extract_video_info(self, post):
        """Extract video information from Reddit post"""
        video_info = None
        url = post.get('url', '')
        
        # Check for Reddit video
        if 'v.redd.it' in url:
            media = post.get('media', {})
            reddit_video = media.get('reddit_video', {})
            
            video_info = {
                'type': 'reddit_video',
                'url': url,
                'fallback_url': reddit_video.get('fallback_url', ''),
                'dash_url': reddit_video.get('dash_url', ''),
                'hls_url': reddit_video.get('hls_url', ''),
                'duration': reddit_video.get('duration', 0),
                'has_audio': reddit_video.get('has_audio', False),
                'height': reddit_video.get('height', 0),
                'width': reddit_video.get('width', 0),
                'is_gif': reddit_video.get('is_gif', False)
            }
        
        # Check for direct video URLs
        elif any(ext in url.lower() for ext in ['.mp4', '.webm', '.mov', '.avi']):
            video_info = {
                'type': 'direct_video',
                'url': url,
                'duration': None  # Will be determined after download
            }
        
        # Check for Imgur gifv
        elif 'imgur.com' in url and 'gifv' in url:
            # Convert gifv to mp4
            mp4_url = url.replace('.gifv', '.mp4')
            video_info = {
                'type': 'imgur_video',
                'url': mp4_url,
                'duration': None
            }
            
        return video_info
    
    def download_and_validate_video(self, video_info, post, filename):
        """Download video with audio and validate duration"""
        try:
            # Create download directory
            download_dir = self.config['paths']['videos']
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            filepath = os.path.join(download_dir, filename)
            
            # Handle different video types
            if video_info['type'] == 'reddit_video':
                success = self.download_reddit_video_with_audio(video_info, filepath)
            else:
                success = self.download_direct_video(video_info, filepath)
            
            if not success:
                return None
            
            # Validate video duration using video processor
            duration = self.video_processor.get_video_duration(filepath)
            max_duration = self.config['reddit']['max_video_duration']
            
            if duration is None:
                self.logger.error(f"Could not determine duration for {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
                
            if duration > max_duration:
                self.logger.info(f"Video too long ({duration}s > {max_duration}s): {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
            
            # Return video metadata in the requested format
            video_metadata = {
                'title': post['title'],
                'url': post['url'],
                'duration': round(duration, 2),
                'filename': filename,
                'filepath': filepath,
                'subreddit': post['subreddit'],
                'has_audio': video_info.get('has_audio', False),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully downloaded and validated: {filename} ({duration:.2f}s) - Audio: {video_info.get('has_audio', False)}")
            return video_metadata
            
        except Exception as e:
            self.logger.error(f"Error downloading video {filename}: {e}")
            # Clean up partial download
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return None
    
    def download_reddit_video_with_audio(self, video_info, filepath):
        """Download Reddit video with audio using yt-dlp"""
        try:
            self.logger.info(f"Downloading Reddit video with audio: {os.path.basename(filepath)}")
            
            # Configure yt-dlp options for Reddit videos
            ydl_opts = {
                'outtmpl': filepath.replace('.mp4', '.%(ext)s'),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'writesubtitles': False,
                'writeautomaticsub': False,
                'quiet': True,   # Reduce yt-dlp output in production
                'no_warnings': True,
                'extractaudio': False,
                'embed_subs': False,
                'writeinfojson': False,
                'writethumbnail': False,
                'prefer_ffmpeg': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
            
            # Use yt-dlp to download with audio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # First try to get info to see available formats
                    info = ydl.extract_info(video_info['url'], download=False)
                    self.logger.info(f"Available formats for Reddit video: {len(info.get('formats', []))}")
                    
                    # Now download
                    ydl.download([video_info['url']])
                    
                except yt_dlp.DownloadError as e:
                    self.logger.warning(f"yt-dlp download failed: {e}")
                    # Try alternative approach using DASH URL if available
                    if video_info.get('dash_url'):
                        self.logger.info("Trying DASH URL approach...")
                        return self.download_reddit_dash_video(video_info, filepath)
                    else:
                        raise e
            
            # Check if file was created (yt-dlp might change extension)
            base_path = filepath.replace('.mp4', '')
            possible_files = [
                filepath,
                base_path + '.mp4',
                base_path + '.webm',
                base_path + '.mkv'
            ]
            
            actual_file = None
            for possible_file in possible_files:
                if os.path.exists(possible_file):
                    actual_file = possible_file
                    break
            
            if actual_file and actual_file != filepath:
                # Rename to expected filename
                os.rename(actual_file, filepath)
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(f"Reddit video downloaded successfully: {file_size} bytes")
                return True
            else:
                self.logger.error(f"Reddit video download failed - file not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading Reddit video with yt-dlp: {e}")
            # Try DASH approach if available
            if video_info.get('dash_url'):
                self.logger.info("Trying DASH URL approach as fallback...")
                return self.download_reddit_dash_video(video_info, filepath)
            else:
                # Final fallback to direct download without audio
                self.logger.info("Falling back to direct video download (no audio)")
                return self.download_direct_video(video_info, filepath)
    
    def download_reddit_dash_video(self, video_info, filepath):
        """Download Reddit video using DASH manifest (with audio)"""
        try:
            import subprocess
            import tempfile
            
            self.logger.info(f"Downloading Reddit video via DASH: {os.path.basename(filepath)}")
            
            dash_url = video_info.get('dash_url')
            if not dash_url:
                return False
            
            # Use ffmpeg to download from DASH manifest
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', dash_url,  # Input DASH manifest
                '-c', 'copy',    # Copy streams without re-encoding
                '-movflags', '+faststart',  # Optimize for streaming
                filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(f"DASH video downloaded successfully: {file_size} bytes")
                return True
            else:
                self.logger.error(f"DASH download failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading via DASH: {e}")
            return False
    
    def download_direct_video(self, video_info, filepath):
        """Download video directly using requests (for non-Reddit videos)"""
        try:
            video_url = video_info['url']
            if video_info['type'] == 'reddit_video' and video_info['fallback_url']:
                video_url = video_info['fallback_url']
            
            self.logger.info(f"Downloading direct video: {os.path.basename(filepath)}")
            
            response = requests.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(f"Direct video downloaded successfully: {file_size} bytes")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading direct video: {e}")
            return False
    
    def get_downloaded_count(self):
        """Get count of downloaded videos from database"""
        try:
            conn = sqlite3.connect('data/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM downloaded_videos')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting download count: {e}")
            return 0
    
    def get_downloaded_by_subreddit(self, subreddit):
        """Get count of downloaded videos for specific subreddit"""
        try:
            conn = sqlite3.connect('data/db.sqlite')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM downloaded_videos WHERE subreddit = ?', (subreddit,))
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error getting download count for r/{subreddit}: {e}")
            return 0 