# InstaReaper - Automated Post Scheduler Documentation

## Overview

The PostScheduler module enables fully automated posting of scraped videos to Instagram at scheduled intervals. This system runs in the background and intelligently selects and posts content based on configurable rules.

## Features

### ✅ Core Functionality
- **Automated Posting**: Schedule posts at regular intervals (default: every 2 hours)
- **Smart Content Selection**: Configurable video filtering and prioritization
- **Rate Limiting**: Prevents Instagram API abuse with built-in delays
- **Quiet Hours**: Skip posting during specified hours (e.g., nighttime)
- **Daily Limits**: Maximum posts per day protection
- **Error Handling**: Comprehensive retry logic and failure recovery

### ✅ GUI Integration
- **Auto Mode Checkbox**: One-click toggle for automated posting
- **Status Monitoring**: Real-time scheduler status display
- **Progress Logging**: All automated actions logged to GUI
- **Configuration Validation**: Pre-flight checks before activation

### ✅ Advanced Configuration
- **Content Filtering**: Duration limits, subreddit preferences/exclusions
- **Caption Generation**: Automated captions with hashtags and source credits
- **Random Delays**: Natural posting patterns to avoid detection
- **Persistence**: Maintains state across application restarts

## File Structure

```
instareaper/
├── core/
│   ├── __init__.py
│   └── scheduler.py              # Main scheduler module
├── config/
│   ├── schedule.json            # Scheduler configuration
│   └── credentials.json         # Instagram credentials
├── data/
│   └── logs/
│       └── scheduler.log        # Scheduler operation logs
└── test_scheduler_integration.py # Testing utility
```

## Configuration

### Schedule Configuration (`config/schedule.json`)

```json
{
    "enabled": false,                    // Master enable/disable switch
    "posting": {
        "frequency_minutes": 120,        // Post every 2 hours
        "randomize_delay": true,         // Add random delays (15-45 min)
        "min_delay_minutes": 15,         // Minimum random delay
        "max_delay_minutes": 45,         // Maximum random delay
        "max_posts_per_day": 12,         // Daily post limit
        "quiet_hours": {
            "enabled": true,             // Enable quiet hours
            "start_hour": 23,            // 11 PM start
            "end_hour": 7                // 7 AM end
        }
    },
    "content_selection": {
        "sort_by": "created_at",         // Sort: created_at, duration, subreddit
        "sort_order": "asc",             // asc or desc
        "filter_by_duration": true,      // Enable duration filtering
        "max_duration_seconds": 60,      // Instagram limit
        "exclude_subreddits": [],        // Skip these subreddits
        "preferred_subreddits": []       // Prioritize these subreddits
    },
    "caption_settings": {
        "use_original_title": true,      // Include video title
        "add_source_credit": true,       // Credit source subreddit
        "add_hashtags": true,            // Include hashtags
        "default_hashtags": ["#viral", "#content", "#reddit", "#instareaper"],
        "max_caption_length": 2000       // Instagram caption limit
    }
}
```

### Key Configuration Options

| Setting | Description | Recommended Value |
|---------|-------------|-------------------|
| `enabled` | Master switch for scheduler | `true` to activate |
| `frequency_minutes` | Time between posts | `120-180` (2-3 hours) |
| `randomize_delay` | Add natural variation | `true` |
| `max_posts_per_day` | Daily posting limit | `8-12` posts |
| `quiet_hours` | Skip nighttime posting | `23:00 - 07:00` |

## Usage

### 1. Initial Setup

```bash
# 1. Configure scheduler
# Edit config/schedule.json:
{
    "enabled": true,
    "posting": {
        "frequency_minutes": 120
    }
}

# 2. Configure Instagram credentials
# Edit config/credentials.json:
{
    "username": "your_instagram_username",
    "password": "your_instagram_password"
}

# 3. Test scheduler
python test_scheduler_integration.py
```

### 2. GUI Usage

1. **Launch Application**: `python run.py`
2. **Scrape Videos**: Use the scraping interface to download content
3. **Enable Auto Mode**: Check the "Auto Mode" checkbox
4. **Monitor Status**: Watch the status label and logs
5. **Manual Override**: Uncheck to stop automated posting

### 3. Programmatic Usage

```python
from core.scheduler import PostScheduler
from data.database import DatabaseHandler
from uploader.instagram_poster import InstagramPoster

# Initialize components
db_handler = DatabaseHandler()
instagram_poster = InstagramPoster()
scheduler = PostScheduler(db_handler, instagram_poster)

# Set up callbacks (optional)
def on_success(video_data, result):
    print(f"Posted: {video_data['title']} - ID: {result['post_id']}")

def on_failure(video_data, result):
    print(f"Failed: {result['message']}")

scheduler.set_callbacks(on_success=on_success, on_failure=on_failure)

# Start automated posting
scheduler.start()

# Stop when done
scheduler.stop()
```

## API Reference

### PostScheduler Class

#### Constructor
```python
PostScheduler(database_handler=None, instagram_poster=None, config_path="config/schedule.json")
```

#### Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `start()` | Start scheduler thread | `bool` (success) |
| `stop()` | Stop scheduler cleanly | `bool` (success) |
| `is_enabled()` | Check if enabled in config | `bool` |
| `is_quiet_hours()` | Check if in quiet period | `bool` |
| `select_next_video()` | Get next video to post | `dict` or `None` |
| `generate_caption(video)` | Create Instagram caption | `str` |
| `get_status()` | Get current scheduler state | `dict` |
| `set_callbacks(...)` | Set GUI callback functions | `None` |

#### Status Dictionary
```python
{
    'running': bool,              # Scheduler thread active
    'enabled': bool,              # Configuration enabled
    'quiet_hours': bool,          # Currently in quiet period
    'posts_today': int,           # Posts made today
    'max_posts_per_day': int,     # Daily limit
    'frequency_minutes': int,     # Posting frequency
    'next_video_available': bool, # Videos ready to post
    'next_video_title': str       # Next video title
}
```

## Logging

### Log Files
- **`data/logs/scheduler.log`**: Scheduler operations, errors, status changes
- **`data/logs/instagram.log`**: Instagram API interactions
- **`data/logs/gui.log`**: GUI events and user interactions

### Log Levels
- **INFO**: Normal operations, posting attempts, status changes
- **WARNING**: Configuration issues, missing videos
- **ERROR**: Posting failures, API errors, system issues

### Sample Log Entries
```
2025-06-12 15:30:00 - PostScheduler - INFO - Scheduler loop started
2025-06-12 15:30:15 - PostScheduler - INFO - Selected video for posting: Funny Cat Video
2025-06-12 15:30:30 - PostScheduler - INFO - Successfully posted video: Funny Cat Video (ID: 12345)
2025-06-12 15:32:00 - PostScheduler - INFO - Next posting scheduled for: 2025-06-12 17:30:00
```

## Safety Features

### Instagram Account Protection
- **Rate Limiting**: Configurable delays between posts
- **Daily Limits**: Prevents exceeding platform limits
- **Random Delays**: Mimics human posting patterns
- **Quiet Hours**: Avoids suspicious nighttime activity
- **Error Recovery**: Handles API failures gracefully

### Content Validation
- **Duration Checking**: Ensures videos meet Instagram requirements
- **File Verification**: Confirms video files exist before posting
- **Duplicate Prevention**: Tracks posted status in database
- **Caption Validation**: Ensures captions meet platform limits

## Troubleshooting

### Common Issues

#### Auto Mode Won't Start
1. **Check Configuration**: Ensure `enabled: true` in schedule.json
2. **Verify Credentials**: Configure Instagram login in credentials.json
3. **Check Videos**: Ensure unposted videos exist in database
4. **Review Logs**: Check scheduler.log for specific errors

#### Posts Not Appearing
1. **Instagram Limits**: Check if daily limit reached
2. **Quiet Hours**: Verify not in quiet period
3. **API Issues**: Check instagram.log for upload errors
4. **Video Format**: Ensure videos meet Instagram requirements

#### Scheduler Stops Unexpectedly
1. **Check Logs**: Review scheduler.log for error messages
2. **API Failures**: Multiple failures may trigger safety stop
3. **System Resources**: Ensure adequate memory/CPU available
4. **Network Issues**: Verify stable internet connection

### Debug Mode

Enable detailed logging by running:
```python
import logging
logging.getLogger('PostScheduler').setLevel(logging.DEBUG)
```

## Performance

### Resource Usage
- **Memory**: ~50MB additional RAM usage
- **CPU**: Minimal, mostly idle between posts
- **Network**: Only during Instagram uploads
- **Storage**: Log files grow ~1MB per day

### Optimization Tips
1. **Batch Processing**: Configure appropriate frequency_minutes
2. **Off-Peak Posting**: Use quiet_hours to avoid peak times
3. **Content Filtering**: Use subreddit preferences to reduce processing
4. **Log Rotation**: Periodically archive old log files

## Security Considerations

### Credential Protection
- **File Permissions**: Ensure config files are not world-readable
- **Version Control**: Add config/ to .gitignore
- **Environment Variables**: Consider using env vars for production
- **Two-Factor Auth**: Instagram 2FA may require app passwords

### Operational Security
- **Posting Patterns**: Use randomization to avoid detection
- **Rate Limits**: Respect Instagram's usage policies
- **Content Guidelines**: Ensure posted content follows platform rules
- **Monitoring**: Watch for unusual API responses or blocks

## Future Enhancements

### Planned Features
- **Multi-Account Support**: Post to multiple Instagram accounts
- **Analytics Integration**: Track post performance metrics
- **Content Curation**: AI-powered content quality assessment
- **Webhook Support**: External notifications for posting events
- **Advanced Scheduling**: Time-of-day optimization based on engagement

### Configuration Improvements
- **Web Interface**: Browser-based configuration management
- **Template System**: Reusable configuration presets
- **A/B Testing**: Experiment with different posting strategies
- **Performance Tuning**: Automatic optimization based on results

## Support

### Getting Help
1. **Test Script**: Run `python test_scheduler_integration.py`
2. **Log Analysis**: Check log files for specific errors
3. **Configuration Validation**: Verify JSON syntax and values
4. **Database Status**: Ensure videos are properly stored

### Best Practices
1. **Start Small**: Begin with low frequency (3-4 hours) and few posts/day
2. **Monitor Results**: Watch engagement and adjust configuration
3. **Regular Maintenance**: Review logs and clean up old files
4. **Backup Configuration**: Save working config files
5. **Test Changes**: Use test accounts for configuration experiments

---

**InstaReaper Scheduler v1.0** - Automated Instagram Posting System 