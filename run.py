#!/usr/bin/env python3
"""
InstaReaper - Reddit Video Scraper
Entry point for the application
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import InstaReaperGUI

def main():
    """Main entry point for InstaReaper"""

    # Create necessary directories
    directories = [
        'data/videos',
        'data/logs',
        'data/thumbnails',
        'config',
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # Initialize PyQt5 Application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look

    # Create and show main window
    window = InstaReaperGUI()
    window.show()

    # Start the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
