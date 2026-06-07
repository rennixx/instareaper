# InstaReaper Scheduler Documentation

## Overview

`core/scheduler.py` contains `PostScheduler`, the background poster used by the GUI `Auto Mode` toggle. It selects the next unposted video from `data/db.sqlite`, generates a caption, uploads through `InstagramPoster`, and persists success back into the database.

## Files and persisted state

- `core/scheduler.py`: scheduler implementation
- `config/schedule.json`: scheduler config file, auto-created with defaults when missing
- `data/db.sqlite`: source of truth for available videos and posted state
- `data/logs/scheduler.log`: scheduler log output
- `tests/test_scheduler_state.py`: checked-in regression coverage for scheduler persistence

Successful scheduler posts call `DatabaseHandler.mark_posted(filename, post_id)`, which updates:

- `posted_to_instagram`
- `instagram_post_id`
- `instagram_posted_at`

## Current selection flow

When the scheduler looks for work, it:

1. loads all videos from `data/db.sqlite`
2. filters out rows already marked `posted_to_instagram`
3. optionally filters by duration
4. applies excluded or preferred subreddit rules
5. sorts by `created_at`, `duration`, or `subreddit`
6. uploads the first remaining candidate

## Current configuration shape

`config/schedule.json` is created from the defaults embedded in `PostScheduler.create_default_config()`. Important sections are:

- `enabled`
- `posting.frequency_minutes`
- `posting.randomize_delay`
- `posting.min_delay_minutes`
- `posting.max_delay_minutes`
- `posting.max_posts_per_day`
- `posting.quiet_hours`
- `content_selection`
- `caption_settings`

Minimal example:

```json
{
  "enabled": true,
  "posting": {
    "frequency_minutes": 120,
    "max_posts_per_day": 12,
    "quiet_hours": {
      "enabled": true,
      "start_hour": 23,
      "end_hour": 7
    }
  }
}
```

## Auto Mode behavior in the GUI

The current GUI path is:

1. launch the app with `python run.py`
2. load or scrape videos into `data/db.sqlite`
3. edit `config/schedule.json` and set `"enabled": true`
4. ensure `config/credentials.json` contains real credentials
5. enable `Auto Mode`

The GUI refuses to start Auto Mode when any of these are true:

- scheduler config is disabled
- `config/credentials.json` is still the template
- there are no unposted videos available

## Effective rate limits

Two layers influence how often posts happen:

- `PostScheduler` controls frequency, quiet hours, randomized pre-post delays, and its own `max_posts_per_day`
- `InstagramPoster` also enforces a minimum 30-minute gap and a process-local limit of 3 uploads per day

In practice, the lower effective limit wins.

## Programmatic usage

```python
from core.scheduler import PostScheduler
from data.database import DatabaseHandler
from uploader.instagram_poster import InstagramPoster

db_handler = DatabaseHandler()
instagram_poster = InstagramPoster()
scheduler = PostScheduler(db_handler, instagram_poster)

status = scheduler.get_status()
print(status)
```

## Logging and verification

Relevant log files:

- `data/logs/scheduler.log`
- `data/logs/instagram.log`
- `data/logs/gui.log`

Useful verification commands for the checked-in source:

```bash
python -m unittest tests.test_scheduler_state -v
python -m py_compile core/scheduler.py data/database.py
```

## Troubleshooting

- Auto Mode does not start: confirm `config/schedule.json` has `"enabled": true`
- GUI asks for credentials: fill `config/credentials.json` even if you previously used `Setup Instagram Login`
- scheduler finds no work: verify unposted rows exist in `data/db.sqlite`
- daily limit reached too early: remember the uploader currently caps successful uploads at 3 per process day
- repeated upload failures: inspect `data/logs/scheduler.log` and `data/logs/instagram.log`
