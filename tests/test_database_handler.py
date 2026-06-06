import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from data.database import DatabaseHandler
from processor.validate import VideoProcessor
from scraper.reddit_scraper import RedditScraper


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


class ScraperMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scraper = RedditScraper.__new__(RedditScraper)
        self.scraper.config = {
            "paths": {"videos": self.temp_dir.name},
            "reddit": {"max_video_duration": 60},
        }
        self.scraper.video_processor = MagicMock()
        self.scraper.logger = MagicMock()
        self.scraper.download_direct_video = MagicMock(return_value=True)
        self.scraper.download_reddit_video_with_audio = MagicMock(return_value=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_downloaded_video_metadata_includes_thumbnail_and_created_at(self):
        self.scraper.video_processor.get_video_duration.return_value = 12.35
        self.scraper.video_processor.generate_thumbnail.return_value = (
            "data/thumbnails/clip_thumb.jpg"
        )

        video_metadata = self.scraper.download_and_validate_video(
            {"type": "direct_video", "url": "https://reddit.example/video.mp4"},
            {
                "title": "Clip",
                "url": "https://reddit.example/post",
                "subreddit": "funny",
            },
            "clip.mp4",
        )

        self.assertEqual(
            video_metadata["thumbnail_path"],
            "data/thumbnails/clip_thumb.jpg",
        )
        self.assertEqual(video_metadata["created_at"], video_metadata["timestamp"])
        self.assertFalse(video_metadata["posted_to_instagram"])


class VideoProcessorThumbnailTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processor = VideoProcessor.__new__(VideoProcessor)
        self.processor.config = {
            "video": {"thumbnail_size": [260, 120]},
            "paths": {"thumbnails": self.temp_dir.name},
        }
        self.processor.logger = MagicMock()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("processor.validate.Image.open")
    @patch("processor.validate.cv2.imwrite", return_value=True)
    @patch("processor.validate.cv2.VideoCapture")
    def test_generate_thumbnail_returns_none_for_invalid_frame_count(
        self,
        video_capture,
        _imwrite,
        image_open,
    ):
        capture = MagicMock()
        capture.isOpened.return_value = True
        capture.get.return_value = 0
        capture.read.return_value = (True, object())
        video_capture.return_value = capture

        image_context = MagicMock()
        image_open.return_value.__enter__.return_value = image_context

        thumbnail_path = self.processor.generate_thumbnail("clip.mp4")

        self.assertIsNone(thumbnail_path)
