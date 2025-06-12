#!/usr/bin/env python3
"""
InstaReaper GUI - Main Window

Enhanced PyQt5 GUI for video scraping, management, and Instagram posting.
Includes video table display, thumbnail previews, media player, and Instagram integration.
"""

import sys
import os
import subprocess
import yaml
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QListWidget, QListWidgetItem, 
                             QLabel, QComboBox, QProgressBar, QTextEdit, QSplitter,
                             QFrame, QScrollArea, QGridLayout, QMessageBox, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QInputDialog, QDialog, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize, QUrl
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from scraper.reddit_scraper import RedditScraper
from processor.validate import VideoProcessor
from data.database import DatabaseHandler
from uploader.instagram_poster import InstagramPoster
from core.scheduler import PostScheduler

class ScrapingThread(QThread):
    progress_update = pyqtSignal(str)
    video_downloaded = pyqtSignal(dict)
    scraping_finished = pyqtSignal()
    
    def __init__(self, niche, limit=10):
        super().__init__()
        self.niche = niche
        self.limit = limit
        self.scraper = RedditScraper()
        
    def run(self):
        try:
            self.progress_update.emit("Starting Reddit scraping...")
            videos = self.scraper.scrape(self.niche, self.limit)
            
            for video_data in videos:
                self.progress_update.emit(f"Downloaded: {video_data.get('title', 'Unknown')[:30]}...")
                self.video_downloaded.emit(video_data)
                
            self.scraping_finished.emit()
        except Exception as e:
            self.progress_update.emit(f"Error: {str(e)}")



class InstaReaperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.setup_logging()
        self.db_handler = DatabaseHandler()
        self.video_processor = VideoProcessor()
        self.scraping_thread = None
        self.media_player = QMediaPlayer()
        self.current_videos = []
        self.instagram_poster = InstagramPoster()
        self.selected_video_index = -1
        self.scheduler = PostScheduler(self.db_handler, self.instagram_poster)
        self.setup_scheduler_callbacks()
        self.init_ui()
        self.load_existing_videos()
        
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open('config.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            # Default config
            self.config = {
                'gui': {'window_size': [1200, 800], 'grid_columns': 3},
                'reddit': {'subreddits': ['memes', 'funny'], 'max_videos_per_scrape': 20},
                'paths': {'logs': 'data/logs', 'videos': 'data/videos'}
            }
    
    def setup_logging(self):
        """Setup logging for GUI operations"""
        try:
            log_dir = self.config['paths']['logs']
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Configure logger specifically for GUI operations
            self.logger = logging.getLogger('InstaReaperGUI')
            self.logger.setLevel(logging.INFO)
            
            # Remove existing handlers to avoid duplicates
            for handler in self.logger.handlers[:]:
                self.logger.removeHandler(handler)
            
            # Create file handler
            log_file = os.path.join(log_dir, 'gui.log')
            file_handler = logging.FileHandler(log_file, mode='a')
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
            self.logger.info("InstaReaper GUI started")
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
    
    def get_dark_theme_stylesheet(self):
        """Return comprehensive dark theme stylesheet"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Central Widget */
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            /* Labels */
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            
            /* Primary Buttons */
            QPushButton {
                background-color: #0d7377;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                min-height: 16px;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5d61;
            }
            QPushButton:disabled {
                background-color: #404040;
                color: #888888;
            }
            
            /* Success/Green Buttons */
            QPushButton[class="success"] {
                background-color: #28a745;
            }
            QPushButton[class="success"]:hover {
                background-color: #34ce57;
            }
            
            /* Danger/Red Buttons */
            QPushButton[class="danger"] {
                background-color: #dc3545;
            }
            QPushButton[class="danger"]:hover {
                background-color: #e4606d;
            }
            
            /* Instagram Button */
            QPushButton[class="instagram"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f09433, stop:0.25 #e6683c, stop:0.5 #dc2743,
                    stop:0.75 #cc2366, stop:1 #bc1888);
                color: #ffffff;
                font-weight: bold;
                padding: 10px 16px;
            }
            QPushButton[class="instagram"]:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5a623, stop:0.25 #f7931e, stop:0.5 #e4405f,
                    stop:0.75 #d6336c, stop:1 #c13584);
            }
            
            /* ComboBox */
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                min-height: 20px;
            }
            QComboBox:hover {
                border-color: #0d7377;
            }
            QComboBox:focus {
                border-color: #14a085;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                selection-background-color: #0d7377;
                outline: none;
            }
            
            /* TextEdit */
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }
            QTextEdit:focus {
                border-color: #0d7377;
            }
            
            /* CheckBox */
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #404040;
            }
            QCheckBox::indicator:unchecked:hover {
                border-color: #0d7377;
            }
            QCheckBox::indicator:checked {
                background-color: #0d7377;
                border: 2px solid #0d7377;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QCheckBox::indicator:checked:hover {
                background-color: #14a085;
            }
            
            /* ProgressBar */
            QProgressBar {
                background-color: #2d2d2d;
                border: 2px solid #404040;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                color: #ffffff;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d7377, stop:1 #14a085);
                border-radius: 4px;
                margin: 2px;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #404040;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #0d7377;
            }
            
            /* ScrollBar */
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #0d7377;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Table Widget */
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                gridline-color: #404040;
                selection-background-color: #0d7377;
                alternate-background-color: #252525;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #404040;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #3a3a3a;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #0d7377;
                border-right: 1px solid #404040;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QHeaderView::section:hover {
                background-color: #2a2a2a;
            }
            
            /* Video Widget */
            QVideoWidget {
                background-color: #2d2d2d;
                border: 2px solid #404040;
                border-radius: 8px;
            }
            
            /* Frame (Separators) */
            QFrame[frameShape="4"] {
                color: #404040;
                background-color: #404040;
                height: 1px;
                border: none;
                margin: 10px 0px;
            }
        """
        
    def init_ui(self):
        self.setWindowTitle("InstaReaper - Reddit Video Scraper")
        window_size = self.config['gui']['window_size']
        self.setGeometry(100, 100, window_size[0], window_size[1])
        # Apply modern dark theme
        self.setStyleSheet(self.get_dark_theme_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)  # Add spacing between panels
        main_layout.setContentsMargins(10, 10, 10, 10)  # Add margins
        central_widget.setLayout(main_layout)
        
        # Left panel (controls)
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)  # Add consistent spacing
        left_panel.setContentsMargins(15, 15, 15, 15)  # Add padding
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(320)  # Slightly wider for better proportions
        left_widget.setStyleSheet("QWidget { background-color: #252525; border-radius: 10px; }")
        
        # Title and stats
        title_label = QLabel("InstaReaper")
        title_label.setFont(QFont('Segoe UI', 22, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; margin: 10px; font-weight: 700; letter-spacing: 1px;")
        left_panel.addWidget(title_label)
        
        # Video count display
        self.video_count_label = QLabel("Videos: 0")
        self.video_count_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        self.video_count_label.setAlignment(Qt.AlignCenter)
        self.video_count_label.setStyleSheet("color: #14a085; margin: 8px; font-weight: 600;")
        left_panel.addWidget(self.video_count_label)
        
        # Niche selection
        niche_label = QLabel("Select Niche:")
        niche_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        niche_label.setStyleSheet("color: #ffffff; margin-top: 15px; margin-bottom: 5px; font-weight: 600;")
        left_panel.addWidget(niche_label)
        
        self.niche_combo = QComboBox()
        self.niche_combo.addItems(self.config['reddit']['subreddits'])
        left_panel.addWidget(self.niche_combo)
        
        # Add separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("QFrame { color: #404040; margin: 10px 0px; }")
        left_panel.addWidget(separator1)
        
        # Buttons
        self.start_button = QPushButton("Start Scraping")
        self.start_button.clicked.connect(self.start_scraping)
        left_panel.addWidget(self.start_button)
        
        self.post_button = QPushButton("Post Now")
        self.post_button.clicked.connect(self.post_now)
        self.post_button.setEnabled(False)  # Will be enabled in future phases
        left_panel.addWidget(self.post_button)
        
        self.folder_button = QPushButton("Open Folder")
        self.folder_button.clicked.connect(self.open_folder)
        left_panel.addWidget(self.folder_button)
        
        # Web authentication button
        self.web_auth_button = QPushButton("🌐 Setup Instagram Login")
        self.web_auth_button.clicked.connect(self.setup_web_authentication)
        self.web_auth_button.setProperty("class", "instagram")
        left_panel.addWidget(self.web_auth_button)
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setProperty("class", "danger")
        left_panel.addWidget(self.exit_button)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("QFrame { color: #404040; margin: 15px 0px; }")
        left_panel.addWidget(separator2)
        
        # Auto Mode section
        auto_mode_label = QLabel("Automated Posting:")
        auto_mode_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        auto_mode_label.setStyleSheet("color: #ffffff; margin-top: 20px; margin-bottom: 5px; font-weight: 600;")
        left_panel.addWidget(auto_mode_label)
        
        self.auto_mode_checkbox = QCheckBox("Auto Mode")
        # Checkbox styling is now handled by the main theme
        self.auto_mode_checkbox.toggled.connect(self.toggle_auto_mode)
        left_panel.addWidget(self.auto_mode_checkbox)
        
        # Scheduler status label
        self.scheduler_status_label = QLabel("Auto Mode: Disabled")
        self.scheduler_status_label.setFont(QFont('Segoe UI', 10))
        self.scheduler_status_label.setStyleSheet("color: #888888; margin: 5px; font-weight: 500;")
        left_panel.addWidget(self.scheduler_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_panel.addWidget(self.progress_bar)
        
        # Add separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setStyleSheet("QFrame { color: #404040; margin: 15px 0px; }")
        left_panel.addWidget(separator3)
        
        # Status log
        status_label = QLabel("Status Log:")
        status_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        status_label.setStyleSheet("color: #ffffff; margin-top: 15px; margin-bottom: 5px; font-weight: 600;")
        left_panel.addWidget(status_label)
        
        self.status_log = QTextEdit()
        self.status_log.setMaximumHeight(150)
        self.status_log.setReadOnly(True)
        left_panel.addWidget(self.status_log)
        
        left_panel.addStretch()
        
        # Right panel (video table and preview)
        right_splitter = QSplitter(Qt.Vertical)
        
        # Video table section
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_widget.setLayout(table_layout)
        
        videos_label = QLabel("Downloaded Videos:")
        videos_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        videos_label.setStyleSheet("color: #ffffff; margin: 10px 0px; font-weight: 600;")
        table_layout.addWidget(videos_label)
        
        # Video table
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(6)  # Thumbnail, Title, Subreddit, Duration, Filename, Instagram
        self.video_table.setHorizontalHeaderLabels(['Thumbnail', 'Title', 'Subreddit', 'Duration', 'Filename', 'Instagram'])
        
        # Configure table
        self.video_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.video_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.video_table.setAlternatingRowColors(True)
        self.video_table.setSortingEnabled(True)
        
        # Configure column widths
        header = self.video_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Thumbnail
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Subreddit
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Filename
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Instagram
        
        self.video_table.setColumnWidth(0, 80)  # Thumbnail column
        
        # Table styling is now handled by the main theme
        
        # Connect selection change
        self.video_table.itemSelectionChanged.connect(self.on_video_selected)
        
        table_layout.addWidget(self.video_table)
        right_splitter.addWidget(table_widget)
        
        # Video preview section
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_widget.setLayout(preview_layout)
        
        preview_label = QLabel("Video Preview:")
        preview_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        preview_label.setStyleSheet("color: #ffffff; margin: 10px 0px; font-weight: 600;")
        preview_layout.addWidget(preview_label)
        
        # Video player
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        self.video_widget.setStyleSheet("background-color: #2d2d2d; border: 2px solid #404040; border-radius: 8px;")
        self.media_player.setVideoOutput(self.video_widget)
        preview_layout.addWidget(self.video_widget)
        
        # Media controls
        controls_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶ Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_button)
        
        # Instagram post button
        self.instagram_button = QPushButton("📸 Post to Instagram")
        self.instagram_button.setEnabled(False)
        self.instagram_button.clicked.connect(self.post_to_instagram)
        self.instagram_button.setProperty("class", "instagram")
        controls_layout.addWidget(self.instagram_button)
        
        controls_layout.addStretch()
        
        # Current video info
        self.current_video_label = QLabel("No video selected")
        self.current_video_label.setFont(QFont('Segoe UI', 10))
        self.current_video_label.setStyleSheet("color: #888888; margin: 5px; font-weight: 500;")
        controls_layout.addWidget(self.current_video_label)
        
        preview_layout.addLayout(controls_layout)
        right_splitter.addWidget(preview_widget)
        
        # Set splitter proportions (table larger than preview)
        right_splitter.setSizes([400, 300])
        
        # Add panels to main layout
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_splitter, 1)
        
        self.log_message("InstaReaper initialized successfully!")
        
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_log.append(f"[{timestamp}] {message}")
        
    def start_scraping(self):
        niche = self.niche_combo.currentText()
        self.log_message(f"Starting scraping for niche: {niche}")
        
        self.start_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        limit = self.config['reddit']['max_videos_per_scrape']
        self.scraping_thread = ScrapingThread(niche, limit=limit)
        self.scraping_thread.progress_update.connect(self.log_message)
        self.scraping_thread.video_downloaded.connect(self.add_video_to_table)
        self.scraping_thread.scraping_finished.connect(self.scraping_finished)
        self.scraping_thread.start()
        
    def add_video_to_table(self, video_data):
        """Add a video to the table display"""
        try:
            # Save to database
            self.db_handler.save_video(video_data)
            
            # Refresh the video table
            self.load_existing_videos()
            
            self.log_message(f"Added video: {video_data['title'][:30]}...")
            
        except Exception as e:
            self.logger.error(f"Error adding video to table: {e}")
            self.log_message(f"Error adding video: {str(e)}")
    
    def on_video_selected(self):
        """Handle video selection in the table"""
        try:
            current_row = self.video_table.currentRow()
            if current_row >= 0 and current_row < len(self.current_videos):
                video = self.current_videos[current_row]
                self.selected_video_index = current_row
                
                # Log selection event
                self.logger.info(f"Video selected: {video['title']} (ID: {video.get('id', 'unknown')})")
                
                # Update UI
                self.current_video_label.setText(f"Selected: {video['title'][:40]}...")
                
                # Load video for preview
                video_path = video.get('filepath', '')
                if not video_path:
                    # Construct path if not stored
                    video_path = os.path.join(self.config['paths']['videos'], 
                                            video.get('filename', ''))
                
                if os.path.exists(video_path):
                    media_content = QMediaContent(QUrl.fromLocalFile(os.path.abspath(video_path)))
                    self.media_player.setMedia(media_content)
                    
                    # Enable controls
                    self.play_button.setEnabled(True)
                    self.stop_button.setEnabled(True)
                    
                    # Check if video can be posted to Instagram (under 60 seconds)
                    duration = video.get('duration', 0)
                    can_post = duration > 0 and duration <= 60.0 and not video.get('posted_to_instagram', False)
                    self.instagram_button.setEnabled(can_post)
                    
                    if not can_post:
                        if duration > 60.0:
                            tooltip = f"Video too long ({duration:.1f}s) - Instagram limit is 60s"
                        elif video.get('posted_to_instagram', False):
                            tooltip = "Video already posted to Instagram"
                        else:
                            tooltip = "Video duration unknown - cannot post"
                        self.instagram_button.setToolTip(tooltip)
                    else:
                        self.instagram_button.setToolTip("Post this video to Instagram")
                    
                    self.log_message(f"Loaded video: {os.path.basename(video_path)}")
                else:
                    self.log_message(f"Video file not found: {video_path}")
                    self.logger.warning(f"Video file not found: {video_path}")
                    self.instagram_button.setEnabled(False)
                    
            else:
                # No video selected
                self.selected_video_index = -1
                self.instagram_button.setEnabled(False)
                self.play_button.setEnabled(False)
                self.stop_button.setEnabled(False)
                    
        except Exception as e:
            self.logger.error(f"Error handling video selection: {e}")
            self.log_message(f"Error selecting video: {str(e)}")
            self.instagram_button.setEnabled(False)
    
    def toggle_playback(self):
        """Toggle video playback"""
        try:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.play_button.setText("▶ Play")
                self.logger.info("Video playback paused")
            else:
                self.media_player.play()
                self.play_button.setText("⏸ Pause")
                self.logger.info("Video playback started")
                
        except Exception as e:
            self.logger.error(f"Error toggling playback: {e}")
            self.log_message(f"Playback error: {str(e)}")
    
    def stop_playback(self):
        """Stop video playback"""
        try:
            self.media_player.stop()
            self.play_button.setText("▶ Play")
            self.logger.info("Video playback stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping playback: {e}")
            self.log_message(f"Stop error: {str(e)}")
    
    def post_to_instagram(self):
        """Post the selected video to Instagram"""
        try:
            # Verify video is selected
            if self.selected_video_index < 0 or self.selected_video_index >= len(self.current_videos):
                self.log_message("❌ No video selected for Instagram posting")
                return
            
            selected_video = self.current_videos[self.selected_video_index]
            video_title = selected_video.get('title', 'Unknown Video')
            
            self.logger.info(f"Instagram posting initiated for: {video_title}")
            
            # Check if already posted
            if selected_video.get('posted_to_instagram', False):
                QMessageBox.warning(self, "Already Posted", 
                                  "This video has already been posted to Instagram.")
                return
            
            # Validate video duration
            duration = selected_video.get('duration', 0)
            if duration > 60.0:
                QMessageBox.warning(self, "Video Too Long", 
                                  f"Video duration ({duration:.1f}s) exceeds Instagram's 60-second limit.")
                return
            
            # Get video file path
            video_path = selected_video.get('filepath', '')
            if not video_path:
                video_path = os.path.join(self.config['paths']['videos'], 
                                        selected_video.get('filename', ''))
            
            if not os.path.exists(video_path):
                QMessageBox.critical(self, "File Not Found", 
                                   f"Video file not found: {os.path.basename(video_path)}")
                self.logger.error(f"Video file not found for Instagram posting: {video_path}")
                return
            
            # Prompt for caption
            caption_dialog = self.get_caption_dialog(selected_video)
            if caption_dialog is None:
                self.log_message("Instagram posting cancelled by user")
                return
            
            # Show progress and disable button
            self.instagram_button.setEnabled(False)
            self.instagram_button.setText("📤 Posting...")
            self.log_message(f"Posting to Instagram: {os.path.basename(video_path)}")
            
            # Attempt to post
            result = self.instagram_poster.upload_video(video_path, caption_dialog)
            
            # Handle result
            if result['success']:
                # Success - update UI and database
                post_id = result['post_id']
                self.logger.info(f"Instagram upload successful - Post ID: {post_id}")
                self.log_message(f"✅ Posted to Instagram! Post ID: {post_id}")
                
                # Update video record in database
                self.update_video_instagram_status(selected_video, post_id, True)
                
                # Update UI
                self.update_video_row_posted_status(self.selected_video_index, True)
                
                # Show success dialog
                QMessageBox.information(self, "Success!", 
                                      f"Video posted successfully to Instagram!\n\n"
                                      f"Post ID: {post_id}\n"
                                      f"Duration: {result['duration']:.1f}s")
                
            else:
                # Failure - show error
                error_msg = result['message']
                self.logger.error(f"Instagram upload failed: {error_msg}")
                self.log_message(f"❌ Instagram upload failed: {error_msg}")
                
                QMessageBox.critical(self, "Upload Failed", 
                                   f"Failed to post video to Instagram:\n\n{error_msg}")
            
        except Exception as e:
            self.logger.error(f"Error in Instagram posting: {e}")
            self.log_message(f"❌ Instagram posting error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while posting to Instagram:\n\n{str(e)}")
            
        finally:
            # Re-enable button and reset text
            self.instagram_button.setText("📸 Post to Instagram")
            # Re-check if button should be enabled
            self.on_video_selected()
    
    def get_caption_dialog(self, video_data):
        """Get caption for Instagram post from user"""
        try:
            # Generate suggested caption
            title = video_data.get('title', 'Great video content')
            subreddit = video_data.get('subreddit', 'reddit')
            duration = video_data.get('duration', 0)
            
            # Create suggested caption
            suggested_caption = f"{title}\n\n"
            suggested_caption += f"Source: r/{subreddit}\n"
            suggested_caption += f"Duration: {duration:.1f}s\n\n"
            suggested_caption += "#viral #content #reddit #instareaper #shortform"
            
            # Limit to Instagram's caption limit (around 2200 characters)
            if len(suggested_caption) > 2000:
                suggested_caption = suggested_caption[:1950] + "...\n\n#viral #content #reddit"
            
            # Show input dialog
            caption, ok = QInputDialog.getMultiLineText(
                self, 
                "Instagram Caption", 
                f"Enter caption for Instagram post:\n\nVideo: {title[:50]}...",
                text=suggested_caption
            )
            
            if ok and caption.strip():
                self.logger.info(f"Caption entered for Instagram post: {len(caption)} characters")
                return caption.strip()
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting caption dialog: {e}")
            return None
    
    def update_video_instagram_status(self, video_data, post_id, posted_status):
        """Update video's Instagram posting status in database"""
        try:
            # Update the video record with Instagram status
            video_id = video_data.get('id')
            if video_id:
                # Add Instagram metadata to video record
                instagram_data = {
                    'posted_to_instagram': posted_status,
                    'instagram_post_id': post_id if posted_status else None,
                    'instagram_posted_at': datetime.now().isoformat()
                }
                
                # Update the current video data
                video_data.update(instagram_data)
                
                # Log the status update
                self.logger.info(f"Updated Instagram status for video ID {video_id}: {posted_status}")
                
        except Exception as e:
            self.logger.error(f"Error updating Instagram status in database: {e}")
    
    def update_video_row_posted_status(self, row_index, posted_status):
        """Update the video table row to show posted status"""
        try:
            if 0 <= row_index < self.video_table.rowCount():
                # Add a new column for Instagram status if it doesn't exist
                if self.video_table.columnCount() < 6:
                    self.video_table.setColumnCount(6)
                    headers = ['Thumbnail', 'Title', 'Subreddit', 'Duration', 'Filename', 'Instagram']
                    self.video_table.setHorizontalHeaderLabels(headers)
                
                # Create status item
                if posted_status:
                    status_item = QTableWidgetItem("✅ Posted")
                    status_item.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    status_item = QTableWidgetItem("")
                
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                self.video_table.setItem(row_index, 5, status_item)
                
                self.logger.info(f"Updated table row {row_index} with Instagram status: {posted_status}")
                
        except Exception as e:
            self.logger.error(f"Error updating video row Instagram status: {e}")
    
    def setup_scheduler_callbacks(self):
        """Setup callback functions for scheduler integration"""
        def on_post_success(video_data, result):
            """Handle successful automated post"""
            try:
                # Update GUI in thread-safe way
                self.log_message(f"✅ Auto-posted: {video_data.get('title', 'Unknown')[:30]}...")
                
                # Refresh video table to show updated status
                self.load_existing_videos()
                
                self.logger.info(f"Automated post successful: {result.get('post_id', 'Unknown ID')}")
                
            except Exception as e:
                self.logger.error(f"Error handling automated post success: {e}")
        
        def on_post_failure(video_data, result):
            """Handle failed automated post"""
            try:
                error_msg = result.get('message', 'Unknown error')
                self.log_message(f"❌ Auto-post failed: {error_msg}")
                self.logger.error(f"Automated post failed: {error_msg}")
                
            except Exception as e:
                self.logger.error(f"Error handling automated post failure: {e}")
        
        def on_status_change(is_running):
            """Handle scheduler status change"""
            try:
                if is_running:
                    self.scheduler_status_label.setText("Auto Mode: Active")
                    self.scheduler_status_label.setStyleSheet("color: #4CAF50; margin: 5px;")
                    self.log_message("🤖 Auto Mode activated")
                else:
                    self.scheduler_status_label.setText("Auto Mode: Disabled")
                    self.scheduler_status_label.setStyleSheet("color: #ccc; margin: 5px;")
                    self.log_message("⏹ Auto Mode deactivated")
                
            except Exception as e:
                self.logger.error(f"Error handling scheduler status change: {e}")
        
        # Set callbacks
        self.scheduler.set_callbacks(
            on_success=on_post_success,
            on_failure=on_post_failure,
            on_status_change=on_status_change
        )
    
    def toggle_auto_mode(self, checked):
        """Toggle automatic posting mode"""
        try:
            if checked:
                # Check if scheduler is configured
                if not self.scheduler.is_enabled():
                    QMessageBox.warning(
                        self, 
                        "Configuration Required", 
                        "Auto Mode is disabled in configuration.\n\n"
                        "Please edit config/schedule.json and set 'enabled': true\n"
                        "to use automatic posting."
                    )
                    self.auto_mode_checkbox.setChecked(False)
                    return
                
                # Check if Instagram credentials are configured
                if (not self.instagram_poster.credentials or 
                    self.instagram_poster.credentials.get('username') == 'your_instagram_username'):
                    QMessageBox.warning(
                        self, 
                        "Instagram Credentials Required", 
                        "Instagram credentials not configured.\n\n"
                        "Please edit config/credentials.json with your\n"
                        "Instagram username and password to use Auto Mode."
                    )
                    self.auto_mode_checkbox.setChecked(False)
                    return
                
                # Check if there are videos to post
                next_video = self.scheduler.select_next_video()
                if not next_video:
                    QMessageBox.information(
                        self, 
                        "No Videos Available", 
                        "No unposted videos available for automatic posting.\n\n"
                        "Scrape some videos first to use Auto Mode."
                    )
                    self.auto_mode_checkbox.setChecked(False)
                    return
                
                # Start scheduler
                if self.scheduler.start():
                    self.logger.info("Auto Mode started by user")
                    status = self.scheduler.get_status()
                    frequency = status.get('frequency_minutes', 120)
                    self.log_message(f"🚀 Auto Mode started (posting every {frequency} minutes)")
                else:
                    QMessageBox.critical(
                        self, 
                        "Failed to Start", 
                        "Failed to start Auto Mode.\n\n"
                        "Check the logs for details."
                    )
                    self.auto_mode_checkbox.setChecked(False)
            else:
                # Stop scheduler
                if self.scheduler.stop():
                    self.logger.info("Auto Mode stopped by user")
                else:
                    self.logger.warning("Failed to stop scheduler cleanly")
                    
        except Exception as e:
            self.logger.error(f"Error toggling auto mode: {e}")
            self.log_message(f"❌ Error toggling Auto Mode: {str(e)}")
            self.auto_mode_checkbox.setChecked(False)
        
    def scraping_finished(self):
        self.start_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log_message("Scraping completed!")
        
    def load_existing_videos(self):
        """Load existing videos from database and populate the table"""
        try:
            videos = self.db_handler.get_all_videos()
            self.current_videos = videos
            
            # Update video count
            self.video_count_label.setText(f"Videos: {len(videos)}")
            
            # Clear and populate table
            self.video_table.setRowCount(len(videos))
            
            for row, video in enumerate(videos):
                try:
                    # Thumbnail column (0)
                    thumbnail_label = QLabel()
                    thumbnail_label.setFixedSize(60, 60)
                    thumbnail_label.setAlignment(Qt.AlignCenter)
                    thumbnail_label.setStyleSheet("border: 1px solid #666; background-color: #555;")
                    
                    # Try to load thumbnail
                    thumbnail_path = video.get('thumbnail_path', '')
                    if thumbnail_path and os.path.exists(thumbnail_path):
                        pixmap = QPixmap(thumbnail_path)
                        scaled_pixmap = pixmap.scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        thumbnail_label.setPixmap(scaled_pixmap)
                    else:
                        thumbnail_label.setText("📹")
                        thumbnail_label.setStyleSheet("border: 1px solid #666; background-color: #555; color: #ccc; font-size: 16px;")
                    
                    self.video_table.setCellWidget(row, 0, thumbnail_label)
                    
                    # Title column (1)
                    title_item = QTableWidgetItem(video.get('title', 'Unknown Title'))
                    title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
                    self.video_table.setItem(row, 1, title_item)
                    
                    # Subreddit column (2)
                    subreddit_item = QTableWidgetItem(f"r/{video.get('subreddit', 'unknown')}")
                    subreddit_item.setFlags(subreddit_item.flags() & ~Qt.ItemIsEditable)
                    self.video_table.setItem(row, 2, subreddit_item)
                    
                    # Duration column (3)
                    duration = video.get('duration', 0)
                    duration_text = f"{duration:.1f}s" if duration else "Unknown"
                    duration_item = QTableWidgetItem(duration_text)
                    duration_item.setFlags(duration_item.flags() & ~Qt.ItemIsEditable)
                    self.video_table.setItem(row, 3, duration_item)
                    
                    # Filename column (4)
                    filename = video.get('filepath', '')
                    if filename:
                        filename = os.path.basename(filename)
                    else:
                        filename = video.get('id', 'unknown.mp4')
                    filename_item = QTableWidgetItem(filename)
                    filename_item.setFlags(filename_item.flags() & ~Qt.ItemIsEditable)
                    self.video_table.setItem(row, 4, filename_item)
                    
                    # Instagram status column (5)
                    instagram_posted = video.get('posted_to_instagram', False)
                    if instagram_posted:
                        instagram_item = QTableWidgetItem("✅ Posted")
                        instagram_item.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    else:
                        instagram_item = QTableWidgetItem("")
                    instagram_item.setFlags(instagram_item.flags() & ~Qt.ItemIsEditable)
                    self.video_table.setItem(row, 5, instagram_item)
                    
                    # Set row height
                    self.video_table.setRowHeight(row, 70)
                    
                except Exception as e:
                    self.logger.error(f"Error adding video row {row}: {e}")
                    continue
            
            self.log_message(f"Loaded {len(videos)} videos from database")
            self.logger.info(f"Successfully loaded {len(videos)} videos into table")
            
        except Exception as e:
            self.logger.error(f"Error loading existing videos: {e}")
            self.log_message(f"Error loading videos: {str(e)}")
            self.video_count_label.setText("Videos: Error")
            
    def post_now(self):
        QMessageBox.information(self, "Feature Coming Soon", 
                              "Instagram posting functionality will be added in the next phase!")
    
    def setup_web_authentication(self):
        """Setup web-based Instagram authentication"""
        try:
            self.log_message("Starting Instagram web authentication...")
            
            # Disable button during setup
            self.web_auth_button.setEnabled(False)
            self.web_auth_button.setText("🔄 Setting up...")
            
            # Setup web authentication
            success, message = self.instagram_poster.setup_web_authentication()
            
            if success:
                self.log_message("✅ Instagram web authentication successful!")
                self.web_auth_button.setText("✅ Instagram Connected")
                
                # Show success message
                QMessageBox.information(
                    self, 
                    "Authentication Success", 
                    "Instagram web authentication completed successfully!\n\n"
                    "You can now post videos to Instagram using the GUI."
                )
            else:
                self.log_message(f"❌ Instagram web authentication failed: {message}")
                self.web_auth_button.setText("🌐 Setup Instagram Login")
                self.web_auth_button.setEnabled(True)
                
                # Show error message
                QMessageBox.warning(
                    self, 
                    "Authentication Failed", 
                    f"Instagram web authentication failed:\n\n{message}\n\n"
                    "Please try again or check your internet connection."
                )
                
        except Exception as e:
            error_msg = f"Error during web authentication: {e}"
            self.log_message(error_msg)
            self.logger.error(error_msg)
            
            self.web_auth_button.setText("🌐 Setup Instagram Login")
            self.web_auth_button.setEnabled(True)
            
            QMessageBox.critical(
                self, 
                "Authentication Error", 
                f"An error occurred during authentication:\n\n{error_msg}"
            )
        
    def open_folder(self):
        videos_folder = self.config['paths']['videos']
        if not os.path.exists(videos_folder):
            os.makedirs(videos_folder)
            
        if sys.platform == "win32":
            os.startfile(videos_folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", videos_folder])
        else:
            subprocess.run(["xdg-open", videos_folder])
            
        self.log_message("Opened videos folder")
        
    def closeEvent(self, event):
        try:
            # Stop scheduler if running
            if self.scheduler and self.scheduler.is_running:
                self.logger.info("Stopping scheduler before exit")
                self.scheduler.stop()
            
            # Check if scraping is in progress
            if self.scraping_thread and self.scraping_thread.isRunning():
                reply = QMessageBox.question(self, 'Exit',
                                           'Scraping is in progress. Are you sure you want to exit?',
                                           QMessageBox.Yes | QMessageBox.No,
                                           QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.scraping_thread.terminate()
                    event.accept()
                else:
                    event.ignore()
            else:
                event.accept()
                
        except Exception as e:
            self.logger.error(f"Error during application close: {e}")
            event.accept()  # Always allow exit even if there's an error 