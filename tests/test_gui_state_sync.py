import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from data.database import DatabaseHandler
from gui.main_window import InstaReaperGUI


class GuiPostingStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "videos.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("gui.main_window.QMessageBox.information")
    def test_post_now_uses_real_instagram_post_flow(self, _message_box):
        gui = InstaReaperGUI.__new__(InstaReaperGUI)
        gui.post_to_instagram = MagicMock()

        gui.post_now()

        gui.post_to_instagram.assert_called_once_with()

    @patch("gui.main_window.QMediaContent")
    @patch("gui.main_window.os.path.exists", return_value=True)
    def test_selecting_postable_video_enables_left_panel_post_button(
        self,
        _path_exists,
        media_content,
    ):
        gui = InstaReaperGUI.__new__(InstaReaperGUI)
        gui.logger = MagicMock()
        gui.log_message = MagicMock()
        gui.media_player = MagicMock()
        gui.current_video_label = MagicMock()
        gui.play_button = MagicMock()
        gui.stop_button = MagicMock()
        gui.instagram_button = MagicMock()
        gui.post_button = MagicMock()
        gui.video_table = MagicMock()
        gui.video_table.currentRow.return_value = 0
        gui.selected_video_index = -1
        gui.config = {"paths": {"videos": self.temp_dir.name}}
        gui.current_videos = [
            {
                "id": 1,
                "title": "Clip",
                "filename": "clip.mp4",
                "filepath": os.path.join(self.temp_dir.name, "clip.mp4"),
                "duration": 15.0,
                "posted_to_instagram": False,
            }
        ]
        media_content.return_value = MagicMock()

        gui.on_video_selected()

        gui.post_button.setEnabled.assert_any_call(True)

    def test_update_video_instagram_status_persists_successful_posts(self):
        db_handler = DatabaseHandler(db_path=self.db_path)
        db_handler.add_video(
            {
                "title": "Clip",
                "filename": "posted.mp4",
                "filepath": os.path.join(self.temp_dir.name, "posted.mp4"),
                "subreddit": "funny",
                "duration": 18.0,
                "url": "https://reddit.example/post",
                "timestamp": "2026-06-06T10:10:00",
            }
        )

        gui = InstaReaperGUI.__new__(InstaReaperGUI)
        gui.db_handler = db_handler
        gui.logger = MagicMock()
        video_data = {
            "id": 1,
            "filename": "posted.mp4",
            "posted_to_instagram": False,
        }

        gui.update_video_instagram_status(video_data, "ig_123", True)

        stored = db_handler.get_all_videos()[0]
        self.assertTrue(stored["posted_to_instagram"])
        self.assertEqual(stored["instagram_post_id"], "ig_123")
        self.assertEqual(video_data["instagram_post_id"], "ig_123")


if __name__ == "__main__":
    unittest.main()
