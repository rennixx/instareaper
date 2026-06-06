import os
import cv2
import subprocess
import yaml
from datetime import datetime
from PIL import Image, ImageFilter
import logging

class VideoProcessor:
    def __init__(self):
        self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Default config
            self.config = {
                'video': {
                    'supported_formats': ['.mp4', '.webm', '.mov', '.avi'],
                    'thumbnail_size': [260, 120],
                    'quality_check': True
                },
                'paths': {
                    'thumbnails': 'data/thumbnails',
                    'logs': 'data/logs'
                }
            }
    
    def setup_logging(self):
        """Setup logging for video processing"""
        log_dir = self.config['paths']['logs']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, 'video_processing.log')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def get_video_duration(self, video_path):
        """Get video duration in seconds using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"Could not open video: {video_path}")
                return None
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            
            if fps <= 0:
                self.logger.error(f"Invalid FPS for video: {video_path}")
                cap.release()
                return None
                
            duration = frame_count / fps
            cap.release()
            
            self.logger.info(f"Video duration: {duration:.2f}s for {video_path}")
            return duration
            
        except Exception as e:
            self.logger.error(f"Error getting video duration: {e}")
            return None
            
    def get_video_duration_ffprobe(self, video_path):
        """Get video duration using ffprobe as fallback"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                self.logger.info(f"Video duration (ffprobe): {duration:.2f}s for {video_path}")
                return duration
            else:
                self.logger.error(f"ffprobe failed for {video_path}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"ffprobe timeout for {video_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error with ffprobe: {e}")
            return None
    
    def generate_thumbnail(self, video_path):
        """Generate thumbnail for video"""
        try:
            # Create thumbnails directory
            thumbnail_dir = self.config['paths']['thumbnails']
            if not os.path.exists(thumbnail_dir):
                os.makedirs(thumbnail_dir)
            
            # Generate thumbnail filename
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_path = os.path.join(thumbnail_dir, f"{video_name}_thumb.jpg")
            
            # Use OpenCV to extract frame
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"Could not open video for thumbnail: {video_path}")
                return None
            
            # Get frame from middle of video
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                self.logger.error(f"Cannot generate thumbnail, invalid frame count: {video_path}")
                cap.release()
                return None
            middle_frame = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                self.logger.error(f"Could not extract frame from {video_path}")
                return None
            
            # Save thumbnail
            cv2.imwrite(thumbnail_path, frame)
            
            # Resize thumbnail using PIL for better quality
            thumbnail_size = tuple(self.config['video']['thumbnail_size'])
            with Image.open(thumbnail_path) as img:
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            self.logger.info(f"Generated thumbnail: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            self.logger.error(f"Error generating thumbnail: {e}")
            return None
    
    def validate_video_format(self, video_path):
        """Validate video format"""
        try:
            file_ext = os.path.splitext(video_path)[1].lower()
            supported_formats = self.config['video']['supported_formats']
            
            is_valid = file_ext in supported_formats
            
            if is_valid:
                self.logger.info(f"Video format valid: {video_path}")
            else:
                self.logger.warning(f"Unsupported video format: {file_ext} for {video_path}")
                
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error validating video format: {e}")
            return False
    
    def check_video_quality(self, video_path):
        """Basic video quality check"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return False
                
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            cap.release()
            
            # Basic quality checks
            min_resolution = 240  # Minimum height
            min_fps = 15
            
            quality_ok = (
                height >= min_resolution and
                fps >= min_fps and
                width > 0 and height > 0
            )
            
            self.logger.info(f"Video quality check: {width}x{height}@{fps}fps - {'PASS' if quality_ok else 'FAIL'}")
            
            return quality_ok
            
        except Exception as e:
            self.logger.error(f"Error checking video quality: {e}")
            return False
    
    def scan_for_watermarks(self, video_path):
        """Basic watermark detection (placeholder for future enhancement)"""
        try:
            # This is a placeholder for watermark detection
            # In a real implementation, you would use computer vision techniques
            # to detect common watermark patterns
            
            # For now, we'll do a simple check for common watermark indicators
            # in the filename or metadata
            
            filename = os.path.basename(video_path).lower()
            watermark_indicators = [
                'tiktok', 'watermark', 'logo', '@', 'instagram',
                'facebook', 'twitter', 'youtube'
            ]
            
            has_watermark = any(indicator in filename for indicator in watermark_indicators)
            
            if has_watermark:
                self.logger.warning(f"Potential watermark detected in: {video_path}")
            else:
                self.logger.info(f"No obvious watermarks detected in: {video_path}")
                
            return has_watermark
            
        except Exception as e:
            self.logger.error(f"Error scanning for watermarks: {e}")
            return False
    
    def validate_video(self, video_path):
        """Complete video validation"""
        try:
            validation_results = {
                'path': video_path,
                'valid_format': self.validate_video_format(video_path),
                'duration': self.get_video_duration(video_path),
                'quality_ok': False,
                'has_watermark': False,
                'overall_valid': False
            }
            
            if validation_results['valid_format'] and validation_results['duration']:
                validation_results['quality_ok'] = self.check_video_quality(video_path)
                validation_results['has_watermark'] = self.scan_for_watermarks(video_path)
                
                # Overall validation
                validation_results['overall_valid'] = (
                    validation_results['valid_format'] and
                    validation_results['duration'] <= 60 and  # Max 60 seconds
                    validation_results['quality_ok']
                )
            
            self.logger.info(f"Video validation complete: {validation_results}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating video: {e}")
            return None 
