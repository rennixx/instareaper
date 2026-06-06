import os
import tempfile
import unittest

from core.scheduler import PostScheduler
from data.database import DatabaseHandler


class StubInstagramPoster:
    def __init__(self, result=None):
        self.result = result or {
            "success": True,
            "post_id": "ig_789",
            "message": "ok",
        }
        self.calls = []

    def upload_video(self, video_path, caption):
        self.calls.append((video_path, caption))
        return self.result


class SchedulerStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "scheduler.db")
        self.config_path = os.path.join(self.temp_dir.name, "schedule.json")
        self.db = DatabaseHandler(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_posts_today_counts_posted_rows(self):
        self.db.add_video(
            {
                "title": "Clip",
                "filename": "scheduled.mp4",
                "filepath": "data/videos/scheduled.mp4",
                "subreddit": "funny",
                "duration": 10.0,
                "url": "https://reddit.example/scheduled",
                "timestamp": "2026-06-06T12:00:00",
            }
        )

        self.db.mark_posted("scheduled.mp4", "ig_456")

        self.assertEqual(self.db.get_posts_today(), 1)

    def test_scheduler_get_posts_today_uses_database_count(self):
        self.db.add_video(
            {
                "title": "Scheduler Clip",
                "filename": "scheduler.mp4",
                "filepath": "data/videos/scheduler.mp4",
                "subreddit": "funny",
                "duration": 10.0,
                "url": "https://reddit.example/scheduler",
                "timestamp": "2026-06-06T12:15:00",
            }
        )
        self.db.mark_posted("scheduler.mp4", "ig_457")
        scheduler = PostScheduler(
            database_handler=self.db,
            instagram_poster=StubInstagramPoster(),
            config_path=self.config_path,
        )

        self.assertEqual(scheduler.get_posts_today(), 1)

    def test_scheduler_post_video_persists_successful_posts(self):
        video_path = os.path.join(self.temp_dir.name, "queued.mp4")
        with open(video_path, "wb") as handle:
            handle.write(b"video")

        self.db.add_video(
            {
                "title": "Queued Clip",
                "filename": "queued.mp4",
                "filepath": video_path,
                "subreddit": "funny",
                "duration": 11.0,
                "url": "https://reddit.example/queued",
                "timestamp": "2026-06-06T12:30:00",
            }
        )
        scheduler = PostScheduler(
            database_handler=self.db,
            instagram_poster=StubInstagramPoster(),
            config_path=self.config_path,
        )

        video_data = self.db.get_all_videos()[0]

        self.assertTrue(scheduler.post_video(video_data))

        stored = self.db.get_all_videos()[0]
        self.assertTrue(stored["posted_to_instagram"])
        self.assertEqual(stored["instagram_post_id"], "ig_789")


if __name__ == "__main__":
    unittest.main()
