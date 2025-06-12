# Instagram Poster Module Documentation

## Overview
The `InstagramPoster` class in `uploader/instagram_poster.py` provides automated Instagram video posting functionality using the `instagrapi` library. It includes secure credential management, rate limiting, and comprehensive logging.

## Features

### ✅ Core Functionality Implemented
- **Secure Authentication**: Uses `config/credentials.json` for secure credential storage
- **Video Upload**: Uploads videos as Instagram Reels with captions
- **Duration Validation**: Checks videos are under 60 seconds (Instagram requirement)
- **Rate Limiting**: 5-10 minute intervals between uploads to avoid spam detection
- **Comprehensive Logging**: All operations logged to `data/logs/instagram.log`
- **Session Management**: Persistent login sessions saved to reduce authentication overhead
- **Error Handling**: Robust error handling with detailed logging

### 🔒 Security Features
- **No hardcoded credentials**: All credentials stored in separate JSON file
- **Session persistence**: Reduces login frequency to avoid detection
- **Rate limiting**: Prevents spam detection and account suspension
- **Secure file handling**: Credentials file excluded from version control

## Installation

### Dependencies
```bash
pip install instagrapi
```

### Required Files
- `uploader/instagram_poster.py` - Main module
- `config/credentials.json` - Secure credential storage (auto-generated template)

## Setup Instructions

### 1. Configure Credentials
Edit `config/credentials.json` with your Instagram credentials:

```json
{
    "username": "your_actual_instagram_username",
    "password": "your_actual_instagram_password",
    "session_file": "data/instagram_session.json",
    "device_settings": {
        "device_id": "",
        "uuid": "",
        "phone_id": "",
        "advertising_id": ""
    }
}
```

**⚠️ Security Note**: Never commit credentials to version control. The file is included in `.gitignore`.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage Examples

### Basic Upload
```python
from uploader.instagram_poster import InstagramPoster

# Initialize poster
poster = InstagramPoster()

# Upload a video
result = poster.upload_video(
    filepath="data/videos/my_video.mp4",
    caption="Check out this awesome video! 🔥 #viral #content #instareaper"
)

# Check result
if result['success']:
    print(f"✅ Upload successful! Post ID: {result['post_id']}")
    print(f"Video duration: {result['duration']:.1f}s")
else:
    print(f"❌ Upload failed: {result['message']}")
```

### Advanced Usage with Error Handling
```python
from uploader.instagram_poster import InstagramPoster
import time

poster = InstagramPoster()

# Check if we can upload (rate limiting)
stats = poster.get_upload_stats()
if not stats['can_upload_now']:
    wait_time = stats['seconds_until_next_upload']
    print(f"⏳ Rate limit active. Wait {wait_time} seconds before uploading.")
    time.sleep(wait_time)

# Validate video before upload
video_path = "data/videos/my_video.mp4"
is_valid, duration = poster.check_video_duration(video_path)

if not is_valid:
    print(f"❌ Video too long: {duration:.1f}s (max 60s)")
else:
    # Proceed with upload
    result = poster.upload_video(
        filepath=video_path,
        caption="Amazing content! #instareaper #viral"
    )
    
    if result['success']:
        print(f"🎉 Success! Post ID: {result['post_id']}")
    else:
        print(f"💥 Failed: {result['message']}")

# Always logout when done
poster.logout()
```

## API Reference

### `InstagramPoster` Class

#### `__init__(config_path: str = "config/credentials.json")`
Initialize the Instagram poster with credential path.

#### `upload_video(filepath: str, caption: str) -> Dict[str, any]`
Upload video to Instagram as a reel.

**Parameters:**
- `filepath`: Path to video file
- `caption`: Caption for the post

**Returns:**
```python
{
    'success': bool,        # True if upload successful
    'post_id': str,         # Instagram post ID (if successful)
    'message': str,         # Status message
    'duration': float       # Video duration in seconds
}
```

#### `check_video_duration(filepath: str) -> Tuple[bool, float]`
Check if video meets Instagram duration requirements.

**Returns:** `(is_valid, duration_seconds)`

#### `check_rate_limit() -> Tuple[bool, int]`
Check if enough time has passed since last upload.

**Returns:** `(can_upload, seconds_to_wait)`

#### `get_upload_stats() -> Dict[str, any]`
Get statistics about uploads and account status.

**Returns:**
```python
{
    'last_upload_time': float,          # Timestamp of last upload
    'can_upload_now': bool,             # Whether can upload now
    'seconds_until_next_upload': int,   # Seconds to wait
    'authenticated': bool,              # Whether logged in
    'last_upload_formatted': str       # Human-readable last upload time
}
```

#### `authenticate() -> bool`
Authenticate with Instagram using stored credentials.

#### `logout()`
Safely logout from Instagram.

## Error Handling

### Common Error Scenarios

1. **Invalid Credentials**
   ```python
   # Error: "Instagram login required - credentials may be invalid"
   # Solution: Check username/password in config/credentials.json
   ```

2. **Rate Limiting**
   ```python
   # Error: "Rate limit: Please wait X seconds before next upload"
   # Solution: Wait for the specified time before retrying
   ```

3. **Video Too Long**
   ```python
   # Error: "Video duration 75.2s exceeds Instagram 60s limit"
   # Solution: Trim video to under 60 seconds
   ```

4. **File Not Found**
   ```python
   # Error: "Video file not found: path/to/video.mp4"
   # Solution: Verify file path and existence
   ```

5. **Instagram Challenges**
   ```python
   # Error: "Instagram challenge required"
   # Solution: Complete verification on Instagram mobile app
   ```

## Logging

All operations are logged to `data/logs/instagram.log` with the following format:
```
2024-01-15 10:30:45 - InstagramPoster - INFO - Successfully authenticated as: @username
2024-01-15 10:31:00 - InstagramPoster - INFO - Starting Instagram upload: video.mp4
2024-01-15 10:31:15 - InstagramPoster - INFO - Upload successful - Post ID: 1234567890
```

### Log Levels
- **INFO**: Normal operations (login, upload, logout)
- **WARNING**: Rate limits, video duration warnings
- **ERROR**: Authentication failures, upload errors

## Rate Limiting

### Built-in Protection
- **Minimum interval**: 5 minutes between uploads
- **Maximum interval**: 10 minutes (randomized to appear more natural)
- **Automatic enforcement**: Upload attempts within interval are blocked

### Best Practices
- Don't upload more than 10-15 videos per day
- Vary upload times to appear more natural
- Use different captions and hashtags for each video
- Monitor Instagram's community guidelines

## Integration with InstaReaper GUI

The Instagram poster can be integrated with the main GUI for seamless video posting:

```python
# In gui/main_window.py
from uploader.instagram_poster import InstagramPoster

class InstaReaperGUI:
    def __init__(self):
        # ... existing code ...
        self.instagram_poster = InstagramPoster()
    
    def post_selected_video(self):
        # Get selected video from table
        selected_video = self.get_selected_video()
        
        if selected_video:
            # Generate caption
            caption = f"Great content from r/{selected_video['subreddit']} #viral #content"
            
            # Upload video
            result = self.instagram_poster.upload_video(
                filepath=selected_video['filepath'],
                caption=caption
            )
            
            # Update GUI with result
            if result['success']:
                self.log_message(f"✅ Posted to Instagram! ID: {result['post_id']}")
            else:
                self.log_message(f"❌ Instagram upload failed: {result['message']}")
```

## Troubleshooting

### Common Issues

1. **"instagrapi not installed"**
   - Solution: `pip install instagrapi`

2. **"Credentials file not found"**
   - Solution: Run the module once to generate template, then edit with real credentials

3. **"Instagram challenge required"**
   - Solution: Complete verification on Instagram mobile app, then retry

4. **"Please wait few minutes"**
   - Solution: Instagram rate limit hit, wait 15-30 minutes before retrying

5. **"Session expired"**
   - Solution: Delete `data/instagram_session.json` to force fresh login

## Security Considerations

### Protecting Your Account
- Use strong, unique passwords
- Enable two-factor authentication on Instagram
- Don't share credentials or session files
- Monitor account activity regularly
- Follow Instagram's community guidelines

### Avoiding Detection
- Don't upload too frequently (max 10-15 videos/day)
- Vary upload timing (don't upload every X minutes exactly)
- Use different captions and hashtags
- Monitor for any Instagram warnings or notifications

## Future Enhancements

### Planned Features
- **Scheduled posting**: Queue videos for future posting
- **Caption templates**: Pre-defined caption formats
- **Hashtag optimization**: Automatic hashtag suggestions
- **Analytics tracking**: Track post performance
- **Bulk upload**: Upload multiple videos with delay
- **Content moderation**: Check content before posting

### Phase 2 Integration
- GUI integration with "Post Now" button
- Visual upload progress indicators
- Post status tracking in video table
- Automated posting schedules

## Support

If you encounter issues:
1. Check the logs in `data/logs/instagram.log`
2. Verify your credentials in `config/credentials.json`
3. Ensure video meets Instagram requirements (under 60s)
4. Check your internet connection
5. Verify Instagram account is in good standing

## Legal Notice

This tool is for educational and legitimate use only. Users are responsible for:
- Complying with Instagram's Terms of Service
- Respecting copyright and intellectual property rights
- Following community guidelines
- Using the tool responsibly and ethically

The developers are not responsible for any account suspensions or violations resulting from misuse of this tool. 