# InstaReaper Finish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconstruct the missing runtime pieces, restore source-level boot, finish the GUI/scheduler/persistence wiring, and leave the repository in a runnable, documented, test-verified state.

**Architecture:** Rebuild the project from the inside out. First restore the missing persistence package and source boot path, then wire metadata and posting state through scraper, GUI, and scheduler, then reconcile build/docs so the checked-in source matches the intended product. Keep tasks small, independently verifiable, and commit only after green checks.

**Tech Stack:** Python 3.12, PyQt5, sqlite3, requests, yt-dlp, OpenCV, Selenium, instagrapi, unittest, git

---

## File Structure

### Existing files to modify

- `run.py`
- `config.yaml`
- `scraper/reddit_scraper.py`
- `processor/validate.py`
- `gui/main_window.py`
- `core/scheduler.py`
- `uploader/instagram_poster.py`
- `build_config.py`
- `build_executable.py`
- `README.md`
- `BUILD_SUMMARY.md`
- `INSTAGRAM_POSTER_DOCUMENTATION.md`
- `SCHEDULER_DOCUMENTATION.md`

### New files to create

- `data/__init__.py`
- `data/database.py`
- `tests/__init__.py`
- `tests/test_database_handler.py`
- `tests/test_boot_and_imports.py`
- `tests/test_build_scripts.py`
- `tests/test_documentation_consistency.py`
- `tests/test_scheduler_state.py`
- `tests/test_gui_state_sync.py`
- `docs/superpowers/plans/2026-06-06-instareaper-task-ledger.md`

### Responsibility boundaries

- `data/database.py`: persistent video metadata, duplicate detection, retrieval, posting-state updates, daily post counts
- `scraper/reddit_scraper.py`: scrape/download/validate and hand normalized metadata to persistence
- `gui/main_window.py`: present persisted state, load preview, update posting status, avoid dead UI actions
- `core/scheduler.py`: choose the next postable video and persist posting outcomes
- `tests/*`: regression coverage for the recovered core behavior

## Task 1: Rebuild the missing persistence package

**Files:**
- Create: `data/__init__.py`
- Create: `data/database.py`
- Create: `tests/__init__.py`
- Create: `tests/test_database_handler.py`

- [ ] **Step 1: Write the failing database tests**

```python
import os
import tempfile
import unittest

from data.database import DatabaseHandler


class DatabaseHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "videos.db")
        self.db = DatabaseHandler(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_read_video(self):
        video = {
            "title": "Clip",
            "filename": "clip.mp4",
            "filepath": "data/videos/clip.mp4",
            "subreddit": "funny",
            "duration": 12.5,
            "url": "https://reddit.example/post",
            "timestamp": "2026-06-06T10:00:00",
        }
        self.assertTrue(self.db.add_video(video))
        videos = self.db.get_all_videos()
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0]["filename"], "clip.mp4")
        self.assertFalse(videos[0]["posted_to_instagram"])

    def test_duplicate_detection_uses_filename(self):
        video = {
            "title": "Clip",
            "filename": "dup.mp4",
            "filepath": "data/videos/dup.mp4",
            "subreddit": "funny",
            "duration": 9.0,
            "url": "https://reddit.example/dup",
            "timestamp": "2026-06-06T10:05:00",
        }
        self.db.add_video(video)
        self.assertTrue(self.db.is_duplicate("dup.mp4"))
        self.assertFalse(self.db.is_duplicate("other.mp4"))

    def test_mark_posted_updates_posting_fields(self):
        video = {
            "title": "Clip",
            "filename": "posted.mp4",
            "filepath": "data/videos/posted.mp4",
            "subreddit": "funny",
            "duration": 14.0,
            "url": "https://reddit.example/posted",
            "timestamp": "2026-06-06T10:10:00",
        }
        self.db.add_video(video)
        self.assertTrue(self.db.mark_posted("posted.mp4", "ig_123"))
        stored = self.db.get_all_videos()[0]
        self.assertTrue(stored["posted_to_instagram"])
        self.assertEqual(stored["instagram_post_id"], "ig_123")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_database_handler -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'data'`

- [ ] **Step 3: Write the minimal persistence implementation**

```python
import os
import sqlite3
from datetime import datetime


class DatabaseHandler:
    def __init__(self, db_path="data/db.sqlite"):
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    filename TEXT NOT NULL UNIQUE,
                    filepath TEXT,
                    thumbnail_path TEXT,
                    subreddit TEXT NOT NULL,
                    duration REAL NOT NULL,
                    url TEXT NOT NULL,
                    has_audio INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    posted_to_instagram INTEGER DEFAULT 0,
                    instagram_post_id TEXT,
                    instagram_posted_at TEXT
                )
                """
            )

    def add_video(self, metadata):
        created_at = metadata.get("timestamp") or metadata.get("created_at") or datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO videos
                (title, filename, filepath, thumbnail_path, subreddit, duration, url, has_audio, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata["title"],
                    metadata["filename"],
                    metadata.get("filepath", ""),
                    metadata.get("thumbnail_path", ""),
                    metadata["subreddit"],
                    metadata["duration"],
                    metadata["url"],
                    1 if metadata.get("has_audio") else 0,
                    created_at,
                ),
            )
            return conn.total_changes > 0

    save_video = add_video

    def is_duplicate(self, filename):
        if not filename:
            return False
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM videos WHERE filename = ?", (filename,)).fetchone()
            return row is not None

    def get_all_videos(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM videos ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_recent(self, limit):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_posted(self, filename, post_id):
        posted_at = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE videos
                SET posted_to_instagram = 1,
                    instagram_post_id = ?,
                    instagram_posted_at = ?
                WHERE filename = ?
                """,
                (post_id, posted_at, filename),
            )
            return conn.total_changes > 0
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_database_handler -v`

Expected: PASS with 3 passing tests

- [ ] **Step 5: Commit**

```bash
git add data/__init__.py data/database.py tests/__init__.py tests/test_database_handler.py
git commit -m "feat: restore database handler persistence layer"
```

## Task 2: Restore source-level boot and import viability

**Files:**
- Modify: `run.py`
- Modify: `config.yaml`
- Create: `tests/test_boot_and_imports.py`

- [ ] **Step 1: Write the failing boot/import tests**

```python
import unittest


class BootImportTests(unittest.TestCase):
    def test_core_modules_import(self):
        import data.database
        import scraper.reddit_scraper
        import processor.validate
        import uploader.instagram_poster
        import core.scheduler
        import gui.main_window
        self.assertTrue(True)

    def test_run_module_exposes_main(self):
        import run
        self.assertTrue(callable(run.main))
```

- [ ] **Step 2: Run the tests to verify the current failure surface**

Run: `python -m unittest tests.test_boot_and_imports -v`

Expected: FAIL if any module still depends on missing runtime paths or inconsistent config defaults

- [ ] **Step 3: Make boot paths consistent**

```python
# in config.yaml
database:
  path: "data/db.sqlite"

paths:
  videos: "data/videos"
  thumbnails: "data/thumbnails"
  logs: "data/logs"
  database: "data/db.sqlite"
```

```python
# in run.py
directories = [
    "data/videos",
    "data/logs",
    "data/thumbnails",
    "config",
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
```

- [ ] **Step 4: Run imports and bytecode verification**

Run: `python -m unittest tests.test_boot_and_imports -v`

Run: `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py`

Expected: PASS and no syntax errors

- [ ] **Step 5: Commit**

```bash
git add run.py config.yaml tests/test_boot_and_imports.py
git commit -m "fix: restore source boot and module imports"
```

## Task 3: Normalize scraped metadata and generate thumbnails

**Files:**
- Modify: `scraper/reddit_scraper.py`
- Modify: `processor/validate.py`
- Modify: `tests/test_database_handler.py`

- [ ] **Step 1: Write a failing metadata-normalization test**

```python
def test_saved_video_can_store_thumbnail_and_created_at(self):
    video = {
        "title": "Clip",
        "filename": "thumb.mp4",
        "filepath": "data/videos/thumb.mp4",
        "thumbnail_path": "data/thumbnails/thumb.jpg",
        "subreddit": "funny",
        "duration": 18.0,
        "url": "https://reddit.example/thumb",
        "timestamp": "2026-06-06T11:00:00",
    }
    self.assertTrue(self.db.add_video(video))
    stored = self.db.get_all_videos()[0]
    self.assertEqual(stored["thumbnail_path"], "data/thumbnails/thumb.jpg")
    self.assertEqual(stored["created_at"], "2026-06-06T11:00:00")
```

- [ ] **Step 2: Run the database test file**

Run: `python -m unittest tests.test_database_handler -v`

Expected: FAIL until scraper/persistence metadata is normalized consistently

- [ ] **Step 3: Wire thumbnail generation and created_at in the scraper**

```python
# in scraper/reddit_scraper.py, after duration validation succeeds
thumbnail_path = self.video_processor.generate_thumbnail(filepath)

video_metadata = {
    "title": post["title"],
    "url": post["url"],
    "duration": round(duration, 2),
    "filename": filename,
    "filepath": filepath,
    "thumbnail_path": thumbnail_path or "",
    "subreddit": post["subreddit"],
    "has_audio": video_info.get("has_audio", False),
    "timestamp": datetime.now().isoformat(),
    "created_at": datetime.now().isoformat(),
    "posted_to_instagram": False,
}
```

```python
# in processor/validate.py
if total_frames <= 0:
    self.logger.error(f"Cannot generate thumbnail, invalid frame count: {video_path}")
    return None
```

- [ ] **Step 4: Re-run persistence verification**

Run: `python -m unittest tests.test_database_handler -v`

Run: `python -m py_compile scraper/reddit_scraper.py processor/validate.py`

Expected: PASS and no syntax errors

- [ ] **Step 5: Commit**

```bash
git add scraper/reddit_scraper.py processor/validate.py tests/test_database_handler.py
git commit -m "feat: persist normalized video metadata and thumbnails"
```

## Task 4: Persist posting status from the GUI and remove dead UI behavior

**Files:**
- Modify: `gui/main_window.py`
- Create: `tests/test_gui_state_sync.py`

- [ ] **Step 1: Write the failing GUI-state sync tests**

```python
import unittest
from data.database import DatabaseHandler


class GuiStateSyncTests(unittest.TestCase):
    def test_database_handler_exposes_mark_posted_contract(self):
        import os
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        db = DatabaseHandler(db_path=os.path.join(temp_dir.name, "gui.db"))
        self.assertTrue(hasattr(db, "mark_posted"))
        temp_dir.cleanup()

    def test_gui_should_use_real_post_action_not_placeholder(self):
        with open("gui/main_window.py", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("self.instagram_button.clicked.connect(self.post_to_instagram)", source)
        self.assertNotIn("Feature Coming Soon", source)
```

- [ ] **Step 2: Run the GUI-state sync tests**

Run: `python -m unittest tests.test_gui_state_sync -v`

Expected: FAIL because the placeholder message still exists

- [ ] **Step 3: Replace the dead path and persist state changes**

```python
# in gui/main_window.py
self.post_button = QPushButton("Post Selected")
self.post_button.clicked.connect(self.post_to_instagram)
self.post_button.setEnabled(False)
```

```python
# in on_video_selected
self.post_button.setEnabled(can_post)
```

```python
# in update_video_instagram_status
filename = video_data.get("filename")
if filename and posted_status:
    self.db_handler.mark_posted(filename, post_id)
```

```python
# in the placeholder handler area, remove the "Feature Coming Soon" branch entirely
```

- [ ] **Step 4: Verify GUI state sync**

Run: `python -m unittest tests.test_gui_state_sync -v`

Run: `python -m py_compile gui/main_window.py`

Expected: PASS and no syntax errors

- [ ] **Step 5: Commit**

```bash
git add gui/main_window.py tests/test_gui_state_sync.py
git commit -m "fix: persist gui posting state and remove dead post action"
```

## Task 5: Finish scheduler persistence and daily post counting

**Files:**
- Modify: `data/database.py`
- Modify: `core/scheduler.py`
- Create: `tests/test_scheduler_state.py`

- [ ] **Step 1: Write the failing scheduler state tests**

```python
import tempfile
import unittest

from data.database import DatabaseHandler
from core.scheduler import PostScheduler


class SchedulerStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = DatabaseHandler(db_path=f"{self.temp_dir.name}/scheduler.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_posts_today_counts_posted_rows(self):
        self.db.add_video({
            "title": "Clip",
            "filename": "scheduled.mp4",
            "filepath": "data/videos/scheduled.mp4",
            "subreddit": "funny",
            "duration": 10.0,
            "url": "https://reddit.example/scheduled",
            "timestamp": "2026-06-06T12:00:00",
        })
        self.db.mark_posted("scheduled.mp4", "ig_456")
        self.assertEqual(self.db.get_posts_today(), 1)
```

- [ ] **Step 2: Run the scheduler-state tests**

Run: `python -m unittest tests.test_scheduler_state -v`

Expected: FAIL because `get_posts_today` support is missing

- [ ] **Step 3: Implement posting-count and scheduler persistence hooks**

```python
# in data/database.py
def get_posts_today(self):
    today = datetime.now().date().isoformat()
    with self._connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM videos
            WHERE posted_to_instagram = 1
              AND substr(instagram_posted_at, 1, 10) = ?
            """,
            (today,),
        ).fetchone()
        return int(row["count"])
```

```python
# in core/scheduler.py
def get_posts_today(self) -> int:
    try:
        return self.database_handler.get_posts_today()
    except Exception as e:
        self.logger.error(f"Error getting today's post count: {e}")
        return 0
```

```python
# in core/scheduler.py, after successful upload
if video_data.get("filename"):
    self.database_handler.mark_posted(video_data["filename"], result["post_id"])
```

- [ ] **Step 4: Verify scheduler state**

Run: `python -m unittest tests.test_scheduler_state -v`

Run: `python -m py_compile core/scheduler.py data/database.py`

Expected: PASS and no syntax errors

- [ ] **Step 5: Commit**

```bash
git add data/database.py core/scheduler.py tests/test_scheduler_state.py
git commit -m "feat: finish scheduler posting persistence"
```

## Task 6: Align build scripts with the real application entrypoint

**Files:**
- Modify: `build_config.py`
- Modify: `build_executable.py`
- Create: `tests/test_build_scripts.py`

- [ ] **Step 1: Write the failing build-entry expectations as a source check**

```python
import unittest


class BuildEntryTests(unittest.TestCase):
    def test_build_config_targets_run_entrypoint(self):
        with open("build_config.py", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("['run.py']", source)
```

- [ ] **Step 2: Run the source-level check**

Run: `python -m unittest tests.test_build_scripts -v`

Expected: Existing tests may pass, but the new expectation should fail until the build target changes

- [ ] **Step 3: Point packaging to the actual entrypoint**

```python
# in build_config.py
a = Analysis(
    ['run.py'],
```

```python
# in build_executable.py, remove the obsolete build-file rewrite step
def create_build_files():
    build_config.create_pyinstaller_spec()
    build_config.create_version_file()


def run_pyinstaller():
    spec_file = build_config.SPEC_FILE
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', spec_file]
```

```python
# in build_executable.py, remove these obsolete assumptions from main/cleanup
# - do not call modify_main_window_for_build()
# - do not remove gui/main_window_build.py in post_build_cleanup()
```

- [ ] **Step 4: Verify build-script consistency**

Run: `python -m py_compile build_config.py build_executable.py run.py`

Expected: PASS with no syntax errors

- [ ] **Step 5: Commit**

```bash
git add build_config.py build_executable.py tests/test_build_scripts.py
git commit -m "fix: align build scripts with run entrypoint"
```

## Task 7: Reconcile docs with the recovered source state

**Files:**
- Modify: `README.md`
- Modify: `BUILD_SUMMARY.md`
- Modify: `INSTAGRAM_POSTER_DOCUMENTATION.md`
- Modify: `SCHEDULER_DOCUMENTATION.md`
- Create: `tests/test_documentation_consistency.py`

- [ ] **Step 1: Write the failing documentation expectations as content checks**

```python
import unittest


class DocumentationConsistencyTests(unittest.TestCase):
    def test_build_summary_should_not_claim_no_credential_storage(self):
        with open("BUILD_SUMMARY.md", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertNotIn("No Credential Storage", source)
```

- [ ] **Step 2: Run the documentation consistency check**

Run: `python -m unittest tests.test_documentation_consistency -v`

Expected: Current docs still conflict with the recovered source and should require edits

- [ ] **Step 3: Update docs to match reality**

```markdown
- clarify that source-level completion, not only packaged output, is now supported
- remove claims that contradict the checked-in auth strategy
- update scheduler docs to reflect actual files and available tests
- describe the real posting path in the GUI
```

- [ ] **Step 4: Verify docs and syntax**

Run: `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py data/database.py`

Expected: PASS, with docs manually matching the recovered behavior

- [ ] **Step 5: Commit**

```bash
git add README.md BUILD_SUMMARY.md INSTAGRAM_POSTER_DOCUMENTATION.md SCHEDULER_DOCUMENTATION.md tests/test_documentation_consistency.py
git commit -m "docs: reconcile project docs with recovered source state"
```

## Self-Review

### Spec coverage

- Reconstructed persistence: covered by Task 1
- Source-level boot: covered by Task 2
- Scraper/metadata integration: covered by Task 3
- GUI posting state: covered by Task 4
- Scheduler critical placeholder removal: covered by Task 5
- Build/doc reality alignment: covered by Tasks 6 and 7
- Incremental tests and commits: built into every task

### Placeholder scan

- No `TODO`, `TBD`, or "implement later" steps remain in the plan
- Verification commands and commit commands are declared for each task

### Type consistency

- `DatabaseHandler` methods used throughout the plan are `add_video`, `save_video`, `is_duplicate`, `get_all_videos`, `get_recent`, `mark_posted`, and `get_posts_today`
- Posting-state field names remain `posted_to_instagram`, `instagram_post_id`, and `instagram_posted_at`

## Execution Handoff

The user has already chosen autonomous hourly execution. The next step is to create the task ledger and the hourly cron automation that reads the ledger, completes at most one task per run, verifies it, commits if green, and never pushes.
