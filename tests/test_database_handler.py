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
