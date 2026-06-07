from pathlib import Path
import unittest


class DocumentationConsistencyTests(unittest.TestCase):
    def read(self, relative_path):
        return Path(relative_path).read_text(encoding="utf-8")

    def test_readme_describes_source_run_and_runtime_paths(self):
        source = self.read("README.md")
        self.assertIn("python run.py", source)
        self.assertIn("data/db.sqlite", source)
        self.assertIn("Post Now", source)

    def test_build_summary_reflects_current_build_workflow(self):
        source = self.read("BUILD_SUMMARY.md")
        self.assertNotIn("No Credential Storage", source)
        self.assertIn("python build_executable.py", source)
        self.assertIn("run.py", source)

    def test_instagram_docs_cover_web_auth_and_credentials_file(self):
        source = self.read("INSTAGRAM_POSTER_DOCUMENTATION.md")
        self.assertIn("Setup Instagram Login", source)
        self.assertIn("config/credentials.json", source)
        self.assertIn("data/instagram_session.json", source)

    def test_scheduler_docs_reference_checked_in_regression_test(self):
        source = self.read("SCHEDULER_DOCUMENTATION.md")
        self.assertNotIn("test_scheduler_integration.py", source)
        self.assertIn("tests/test_scheduler_state.py", source)
        self.assertIn("data/db.sqlite", source)


if __name__ == "__main__":
    unittest.main()
