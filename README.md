# InstaReaper

InstaReaper is a source-runnable PyQt desktop app that scrapes Reddit videos, validates them, stores their metadata in SQLite, and posts selected clips to Instagram manually or on a schedule.

## Checked-in application scope

- `run.py` is the source entrypoint for the desktop application.
- `data/database.py` persists video metadata and posting state in `data/db.sqlite`.
- `scraper/reddit_scraper.py` downloads videos and stores normalized metadata, including thumbnail paths.
- `gui/main_window.py` exposes both manual posting actions: the left-panel `Post Now` button and the selected-video `Post to Instagram` button.
- `core/scheduler.py` automates posting from persisted state in `data/db.sqlite`.

## Requirements

- Python 3.12
- Windows is the primary target for the GUI and packaging scripts
- Dependencies from `requirements.txt`

## Install and run from source

```bash
pip install -r requirements.txt
python run.py
```

On first launch, `run.py` creates these runtime directories when they do not already exist:

- `data/videos`
- `data/logs`
- `data/thumbnails`
- `config`

The first GUI launch also initializes missing runtime config files through the checked-in modules:

- `config/credentials.json` is created as a template by `InstagramPoster` when missing.
- `config/schedule.json` is created with defaults by `PostScheduler` when missing.

## Runtime files and state

- `config.yaml`: checked-in application defaults for paths, GUI sizing, and Reddit settings
- `config/credentials.json`: Instagram username/password template for traditional auth and GUI Auto Mode validation
- `config/schedule.json`: scheduler configuration created on demand
- `data/db.sqlite`: persisted video catalog and Instagram posting state
- `data/instagram_session.json`: saved Instagram session after successful authentication
- `data/logs/*.log`: GUI, scheduler, and Instagram log files

The credential and session files above are gitignored and are expected to stay local.

## Typical workflow

1. Launch the app with `python run.py`.
2. If you want browser-based authentication, click `Setup Instagram Login` and complete the web flow.
3. Scrape videos from one of the configured subreddits.
4. Select a video and post it manually with `Post Now` or `Post to Instagram`.
5. Review the updated posted status in the table after a successful upload.

## Automated posting

To use Auto Mode from the GUI:

1. Edit `config/schedule.json` and set `"enabled": true`.
2. Keep `config/credentials.json` populated with a real username and password, because the GUI checks that file before starting Auto Mode.
3. Launch `python run.py`, scrape or load unposted videos, and enable `Auto Mode`.

Current posting limits come from two layers:

- `PostScheduler` uses `config/schedule.json` for frequency, quiet hours, subreddit filtering, and `max_posts_per_day`.
- `InstagramPoster` currently enforces a minimum 30-minute delay between successful uploads and a process-local cap of 3 uploads per day.

Successful manual or automated uploads persist `posted_to_instagram`, `instagram_post_id`, and `instagram_posted_at` in `data/db.sqlite`.

## Build scripts

The packaging scripts target the same source entrypoint used for local development:

```bash
python build_config.py
python build_executable.py
python create_installer.py
```

- `build_config.py` generates a PyInstaller spec for `run.py`.
- `build_executable.py` builds `dist/InstaReaper.exe` and a portable package when its dependency checks pass.
- `create_installer.py` is the optional installer step after a successful executable build.

## Verification shortcuts

Useful repo-level checks:

```bash
python -m unittest tests.test_boot_and_imports -v
python -m unittest tests.test_database_handler -v
python -m unittest tests.test_scheduler_state -v
python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py data/database.py
```
