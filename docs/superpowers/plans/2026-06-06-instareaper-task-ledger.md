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
- Status: pending
- Dependencies: none
- Verification:
  - `python -m unittest tests.test_database_handler -v`
- Expected Commit: `feat: restore database handler persistence layer`
- Notes:
  - Recreate `data/database.py` and `data/__init__.py`
  - Provide schema, duplicate detection, fetch methods, and posting-state updates

## Task IR-002

- Title: Restore source boot and module imports
- Status: pending
- Dependencies: IR-001
- Verification:
  - `python -m unittest tests.test_boot_and_imports -v`
  - `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py`
- Expected Commit: `fix: restore source boot and module imports`
- Notes:
  - Make `run.py` create required runtime directories
  - Align `config.yaml` database path with the reconstructed persistence layer

## Task IR-003

- Title: Persist normalized scraped metadata and thumbnails
- Status: pending
- Dependencies: IR-001, IR-002
- Verification:
  - `python -m unittest tests.test_database_handler -v`
  - `python -m py_compile scraper/reddit_scraper.py processor/validate.py`
- Expected Commit: `feat: persist normalized video metadata and thumbnails`
- Notes:
  - Add `thumbnail_path`, `created_at`, and default posting fields to scraper output
  - Ensure thumbnail generation fails safely on invalid frame counts

## Task IR-004

- Title: Persist GUI posting state and remove dead post action
- Status: pending
- Dependencies: IR-001, IR-002
- Verification:
  - `python -m unittest tests.test_gui_state_sync -v`
  - `python -m py_compile gui/main_window.py`
- Expected Commit: `fix: persist gui posting state and remove dead post action`
- Notes:
  - Replace the left-panel placeholder action with the real post flow
  - Persist successful posting state through `DatabaseHandler`

## Task IR-005

- Title: Finish scheduler posting persistence
- Status: pending
- Dependencies: IR-001, IR-002, IR-003
- Verification:
  - `python -m unittest tests.test_scheduler_state -v`
  - `python -m py_compile core/scheduler.py data/database.py`
- Expected Commit: `feat: finish scheduler posting persistence`
- Notes:
  - Implement real daily post counting
  - Persist successful scheduler posts through the database handler

## Task IR-006

- Title: Align build scripts with run entrypoint
- Status: pending
- Dependencies: IR-002
- Verification:
  - `python -m py_compile build_config.py build_executable.py run.py`
- Expected Commit: `fix: align build scripts with run entrypoint`
- Notes:
  - Package from `run.py`
  - Remove assumptions that `gui/main_window.py` is the application script

## Task IR-007

- Title: Reconcile docs with recovered source state
- Status: pending
- Dependencies: IR-001, IR-002, IR-003, IR-004, IR-005, IR-006
- Verification:
  - `python -m py_compile run.py gui/main_window.py scraper/reddit_scraper.py core/scheduler.py data/database.py`
- Expected Commit: `docs: reconcile project docs with recovered source state`
- Notes:
  - Update README, build summary, Instagram poster docs, and scheduler docs
  - Remove claims that contradict the checked-in source behavior
