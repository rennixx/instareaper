# InstaReaper Task Ledger

Use this ledger as the authoritative run-state file for the hourly finisher automation.

## Rules

- Pick the first task with `status: pending` whose dependencies are all `completed`.
- Complete at most one task per run.
- Run every listed verification command before committing.
- If verification fails and cannot be repaired within task scope, leave the task `pending` and append a note.
- If the same blocker repeats across three runs, set `status: blocked` and explain why.
- Never push.

---

## Task IR-001

- Title: Restore database handler persistence layer
- Status: completed
- Dependencies: none
- Verification:
  - `python -m unittest tests.test_database_handler -v`
- Expected Commit: `feat: restore database handler persistence layer`
- Notes:
  - Recreated `data/database.py` and `data/__init__.py` with SQLite-backed video persistence
  - Verified with `python -m unittest tests.test_database_handler -v` and `python -m py_compile data/database.py tests/test_database_handler.py`

## Task IR-002

- Title: Restore source boot and module imports
- Status: completed
- Dependencies: IR-001
- Verification:
  - `python -m unittest tests.test_boot_and_imports -v`
  - `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py`
- Expected Commit: `fix: restore source boot and module imports`
- Notes:
  - Added `tests/test_boot_and_imports.py` to verify direct imports and `run.main`
  - Updated `run.py` and `config.yaml` to create the runtime directories and point at `data/db.sqlite`
  - Removed the import-time Unicode console print from `uploader/instagram_poster.py` so module imports succeed on this Windows environment

## Task IR-003

- Title: Persist normalized scraped metadata and thumbnails
- Status: completed
- Dependencies: IR-001, IR-002
- Verification:
  - `python -m unittest tests.test_database_handler -v`
  - `python -m py_compile scraper/reddit_scraper.py processor/validate.py`
- Expected Commit: `feat: persist normalized video metadata and thumbnails`
- Notes:
  - Added regression coverage for normalized scraper metadata and zero-frame thumbnail generation
  - Updated the scraper to emit `thumbnail_path`, `created_at`, and default posting state using one shared timestamp
  - Guarded thumbnail generation against invalid frame counts before frame extraction

## Task IR-004

- Title: Persist GUI posting state and remove dead post action
- Status: completed
- Dependencies: IR-001, IR-002
- Verification:
  - `python -m unittest tests.test_gui_state_sync -v`
  - `python -m py_compile gui/main_window.py`
- Expected Commit: `fix: persist gui posting state and remove dead post action`
- Notes:
  - Added `tests/test_gui_state_sync.py` to cover the left-panel post button, selection-state enablement, and persistence updates
  - Wired the left-panel `Post Now` button into the real Instagram post flow and kept it synchronized with postability state
  - Persisted successful GUI posts through `DatabaseHandler.mark_posted` and verified with GUI, import, and database regression checks

## Task IR-005

- Title: Finish scheduler posting persistence
- Status: completed
- Dependencies: IR-001, IR-002, IR-003
- Verification:
  - `python -m unittest tests.test_scheduler_state -v`
  - `python -m py_compile core/scheduler.py data/database.py`
- Expected Commit: `feat: finish scheduler posting persistence`
- Notes:
  - Added `tests/test_scheduler_state.py` to cover database daily counts, scheduler count delegation, and persisted scheduler post success
  - Implemented `DatabaseHandler.get_posts_today()` and wired `PostScheduler.get_posts_today()` to use the database count
  - Persisted successful scheduler uploads with `DatabaseHandler.mark_posted()` and verified with scheduler, compile, and database regression checks

## Task IR-006

- Title: Align build scripts with run entrypoint
- Status: completed
- Dependencies: IR-002
- Verification:
  - `python -m py_compile build_config.py build_executable.py run.py`
- Expected Commit: `fix: align build scripts with run entrypoint`
- Notes:
  - Added `tests/test_build_scripts.py` to lock the PyInstaller entrypoint to `run.py` and reject build-only main-window rewrites
  - Updated `build_config.py` to generate the spec against `run.py`
  - Removed the `gui/main_window_build.py` rewrite path from `build_executable.py` and verified with `python -m unittest tests.test_build_scripts -v` plus the task's `py_compile` check

## Task IR-007

- Title: Reconcile docs with recovered source state
- Status: completed
- Dependencies: IR-001, IR-002, IR-003, IR-004, IR-005, IR-006
- Verification:
  - `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py data/database.py`
- Expected Commit: `docs: reconcile project docs with recovered source state`
- Notes:
  - Added `tests/test_documentation_consistency.py` to lock the README, build summary, Instagram poster docs, and scheduler docs to the current checked-in source behavior
  - Rewrote the four docs to describe `python run.py`, `data/db.sqlite`, the real GUI posting actions, the current authentication flow, and the checked-in scheduler regression test path
  - Verified with `python -m unittest tests.test_documentation_consistency -v` and the task's `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py data/database.py` check
