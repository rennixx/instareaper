# InstaReaper Build Workflow Summary

This repository does not check in built binaries. The build scripts package the current source tree, whose desktop entrypoint is `run.py`.

## Current build pipeline

1. `python build_config.py`
   - Generates the PyInstaller spec file and Windows version metadata.
   - The generated spec targets `run.py`.
2. `python build_executable.py`
   - Verifies build dependencies.
   - Cleans previous `build/` and `dist/` directories.
   - Regenerates the PyInstaller spec and version file.
   - Runs `python -m PyInstaller --clean <spec>`.
   - Verifies `dist/InstaReaper.exe`.
   - Creates `dist/InstaReaper_Portable/`.
3. `python create_installer.py`
   - Optional follow-on step for installer packaging after a successful executable build.

## Build prerequisites

The build helper checks for these packages in addition to the application requirements:

- `pyinstaller`
- `pillow`
- `PyQt5`
- `instagrapi`
- `selenium`
- `webdriver-manager`
- `opencv-python`
- `yt-dlp`

Typical setup:

```bash
pip install -r requirements.txt
pip install pyinstaller pillow PyQt5 instagrapi selenium webdriver-manager opencv-python yt-dlp
```

## Expected outputs after a successful build

`build_executable.py` is expected to create:

- `dist/InstaReaper.exe`
- `dist/InstaReaper_Portable/`
- a copied `README.md`
- `assets/`
- empty `data/videos` and `data/logs` directories inside the portable package

The application itself creates `data/thumbnails` and other runtime files on first launch.

## Runtime and authentication notes

Packaging does not change the checked-in authentication model:

- `config/credentials.json` is still used for traditional username/password authentication and for GUI Auto Mode validation.
- `data/instagram_session.json` is still used for persisted Instagram sessions.
- The GUI still exposes `Setup Instagram Login` for browser-based session setup.

Both `config/credentials.json` and `data/instagram_session.json` are gitignored local files.

## Recommended verification

Before starting a packaging run, confirm the source tree still imports and compiles cleanly:

```bash
python -m unittest tests.test_build_scripts -v
python -m unittest tests.test_boot_and_imports -v
python -m py_compile build_config.py build_executable.py run.py
```

If those checks pass, the build scripts are aligned with the current `run.py` application entrypoint.
