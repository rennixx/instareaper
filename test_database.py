#!/usr/bin/env python3
"""
Test script for VideoDatabase
Demonstrates usage of the database module
"""

import sys
import os
from datetime import datetime

# Add current directory to path so we can import our modules
sys.path.append('.')

from data.database import DatabaseHandler

def test_database():
    """Test the VideoDatabase functionality"""
    
    print("🗃️  InstaReaper VideoDatabase Test")
    print("=" * 40)
    
    # Initialize database
    db = DatabaseHandler()
    
    # Test sample metadata (matching Reddit scraper format)
    sample_videos = [
        {
            'title': 'Funny meme compilation',
            'filename': '1703123456_funny_meme_compilation.mp4',
            'subreddit': 'memes',
            'duration': 45.2,
            'url': 'https://reddit.com/r/memes/example1',
            'timestamp': datetime.now().isoformat()
        },
        {
            'title': 'Dank video content',
            'filename': '1703123500_dank_video_content.mp4', 
            'subreddit': 'dankmemes',
            'duration': 38.7,
            'url': 'https://reddit.com/r/dankmemes/example2',
            'timestamp': datetime.now().isoformat()
        },
        {
            'title': 'Hilarious short clip',
            'filename': '1703123600_hilarious_short_clip.mp4',
            'subreddit': 'funny',
            'duration': 22.1,
            'url': 'https://reddit.com/r/funny/example3', 
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    print("📊 Initial database stats:")
    print(f"   Total videos: {len(db.get_all_videos())}")
    
    print("\n➕ Testing add_video() method:")
    for i, video in enumerate(sample_videos, 1):
        # Check for duplicate first
        if db.is_duplicate(video['filename']):
            print(f"   Video {i}: ⚠️  Already exists - {video['filename']}")
        else:
            # Add video
            if db.add_video(video):
                print(f"   Video {i}: ✅ Added - {video['title'][:30]}...")
            else:
                print(f"   Video {i}: ❌ Failed - {video['title'][:30]}...")
    
    print(f"\n📊 Updated database stats:")
    print(f"   Total videos: {len(db.get_all_videos())}")
    
    print("\n🔍 Testing is_duplicate() method:")
    test_filenames = [
        '1703123456_funny_meme_compilation.mp4',  # Should exist
        'nonexistent_video.mp4'  # Should not exist
    ]
    
    for filename in test_filenames:
        is_dup = db.is_duplicate(filename)
        status = "✅ Duplicate" if is_dup else "❌ Not found"
        print(f"   {filename}: {status}")
    
    print("\n📋 Testing get_all_videos() method:")
    all_videos = db.get_all_videos()
    print(f"   Retrieved {len(all_videos)} total videos:")
    for video in all_videos:
        print(f"     • {video['filename']} - {video['duration']}s from r/{video['subreddit']}")
    
    print("\n⏰ Testing get_recent() method (limit 2):")
    recent_videos = db.get_recent(2)
    print(f"   Retrieved {len(recent_videos)} recent videos:")
    for video in recent_videos:
        print(f"     • {video['title'][:40]}... ({video['duration']}s)")
    
    print("\n🏷️  Testing database statistics:")
    all_videos = db.get_all_videos()
    subreddits = {}
    for video in all_videos:
        subreddit = video.get('subreddit', 'unknown')
        subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
    
    for subreddit, count in subreddits.items():
        print(f"   r/{subreddit}: {count} videos")
    
    print(f"\n📈 Final database stats:")
    print(f"   Total videos: {len(all_videos)}")
    print(f"   Database file: data/db.sqlite")
    print(f"   Log file: data/logs/database.log")
    
    print("\n🎉 Database test completed!")

def test_error_handling():
    """Test error handling with invalid data"""
    
    print("\n🔧 Testing error handling:")
    db = DatabaseHandler()
    
    # Test with missing required fields
    invalid_metadata = {
        'title': 'Test video',
        'filename': 'test.mp4'
        # Missing: subreddit, duration, url, timestamp
    }
    
    result = db.add_video(invalid_metadata)
    print(f"   Invalid metadata: {'❌ Rejected' if not result else '⚠️  Unexpectedly accepted'}")
    
    # Test duplicate check with None/empty filename
    try:
        is_dup = db.is_duplicate("")
        print(f"   Empty filename check: {'✅ Handled' if not is_dup else '⚠️  Unexpected result'}")
    except Exception as e:
        print(f"   Empty filename check: ❌ Error - {e}")

if __name__ == "__main__":
    test_database()
    test_error_handling() 