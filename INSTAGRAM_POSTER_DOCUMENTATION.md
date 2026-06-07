# Instagram Poster Module Documentation

## Overview

`uploader/instagram_poster.py` contains the `InstagramPoster` class used by both the GUI and the scheduler to upload reels with `instagrapi`.

The checked-in implementation currently provides:

- session reuse through `data/instagram_session.json`
- optional browser-session bootstrap from the GUI `Setup Instagram Login` flow
- fallback username/password authentication from `config/credentials.json`
- duration validation with OpenCV
- upload logging to `data/logs/instagram.log`
- conservative rate limiting inside the uploader itself

## Authentication order

`InstagramPoster.authenticate()` attempts login in this order:

1. load an existing session from `data/instagram_session.json`
2. reuse browser cookies captured by `InstagramWebAuth` if available
3. fall back to username/password login from `config/credentials.json`

If `config/credentials.json` does not exist, the module creates a template file automatically.

## Local files used by the module

- `config/credentials.json`: username/password template and optional session-file override
- `data/instagram_session.json`: persisted instagrapi session
- `data/logs/instagram.log`: upload and authentication log

All three are local runtime files. The credentials and session files are gitignored.

## Current upload rules

The source code currently enforces these limits:

- videos longer than 60 seconds are rejected
- successful uploads must be at least 30 minutes apart
- the uploader keeps a process-local maximum of 3 successful uploads per day
- a short random delay is added before and after each upload attempt

These values come from the current implementation, not from external docs.

## GUI integration

`gui/main_window.py` wires the poster into three user-facing flows:

- `Setup Instagram Login` for browser-based authentication
- `Post Now` in the left control panel
- `Post to Instagram` for the currently selected video in the preview panel

Both manual posting buttons call the same `post_to_instagram()` path. On success, the GUI persists `posted_to_instagram`, `instagram_post_id`, and `instagram_posted_at` through `DatabaseHandler.mark_posted()`.

## Scheduler integration

`core/scheduler.py` reuses the same poster instance for Auto Mode. Two details matter in the current source tree:

- the scheduler can reuse `data/instagram_session.json` after a successful manual or browser-authenticated login
- the GUI still requires a non-template `config/credentials.json` before it lets the user enable Auto Mode

That means browser auth is useful, but the credentials file is still part of the checked-in Auto Mode flow.

## Minimal usage example

```python
from uploader.instagram_poster import InstagramPoster

poster = InstagramPoster()
success = poster.authenticate()

if success:
    result = poster.upload_video(
        filepath="data/videos/example.mp4",
        caption="Example reel caption"
    )
    print(result)
    poster.logout()
```

## Troubleshooting

- `config/credentials.json` missing: start the app once and fill in the generated template
- browser login succeeded but uploads still fail: remove `data/instagram_session.json` and authenticate again
- Auto Mode stays disabled: confirm `config/credentials.json` has real credentials and `config/schedule.json` has `"enabled": true`
- upload rejected for duration: trim the clip below 60 seconds
- import-time warning about `instagrapi`: install the package from `requirements.txt`

## Verification

Useful checks for the checked-in module:

```bash
python -m unittest tests.test_boot_and_imports -v
python -m py_compile uploader/instagram_poster.py
```
