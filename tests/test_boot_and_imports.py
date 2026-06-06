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
