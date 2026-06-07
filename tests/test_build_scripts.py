import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

import build_config


class BuildEntryTests(unittest.TestCase):
    def test_build_config_targets_run_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with contextlib.redirect_stdout(io.StringIO()):
                    build_config.create_pyinstaller_spec()
                spec_path = Path(temp_dir) / build_config.SPEC_FILE
                spec_source = spec_path.read_text(encoding="utf-8")
            finally:
                os.chdir(original_cwd)

        self.assertIn("['run.py']", spec_source)

    def test_build_executable_does_not_use_build_only_main_window_copy(self):
        source = Path("build_executable.py").read_text(encoding="utf-8")
        self.assertNotIn("main_window_build.py", source)
        self.assertNotIn("modify_main_window_for_build", source)


if __name__ == "__main__":
    unittest.main()
