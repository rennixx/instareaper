#!/usr/bin/env python3
"""
Integration example: Reddit Scraper + VideoDatabase
Shows how the scraper and database work together
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from scraper.reddit_scraper import RedditScraper
from data.database import DatabaseHandler

def scrape_and_store_example():
    """Example of scraping videos and storing them in the database"""
    
    print("🚀 InstaReaper Integration Example")
    print("=" * 45)
    
    # Initialize components
    print("🔧 Initializing components...")
    scraper = RedditScraper()
    db = DatabaseHandler()
    
    # Check initial state
    initial_count = len(db.get_all_videos())
    print(f"📊 Initial database count: {initial_count} videos")
    
    # Define subreddits to scrape
    subreddits = ['memes', 'funny']
    
    for subreddit in subreddits:
        print(f"\n📡 Scraping r/{subreddit}...")
        
        try:
            # Scrape videos (limit to 2 for demo)
            videos = scraper.scrape(subreddit, limit=2)
            
            print(f"   Found {len(videos)} new videos")
            
            # Process each scraped video
            for video in videos:
                print(f"\n   Processing: {video['title'][:40]}...")
                
                # Check if already in database (double-check)
                if db.is_duplicate(video['filename']):
                    print(f"     ⚠️  Already exists in database")
                    continue
                
                # Add to database
                if db.add_video(video):
                    print(f"     ✅ Added to database")
                    print(f"        Duration: {video['duration']}s")
                    print(f"        Filename: {video['filename']}")
                else:
                    print(f"     ❌ Failed to add to database")
                    
        except Exception as e:
            print(f"   ❌ Error scraping r/{subreddit}: {e}")
    
    # Show final results
    final_count = len(db.get_all_videos())
    new_videos = final_count - initial_count
    
    print(f"\n📈 Results Summary:")
    print(f"   Videos before: {initial_count}")
    print(f"   Videos after: {final_count}")
    print(f"   New videos added: {new_videos}")
    
    # Show recent videos
    print(f"\n⏰ Recent videos in database:")
    recent_videos = db.get_recent(5)
    for i, video in enumerate(recent_videos, 1):
        print(f"   {i}. {video['title'][:35]}... ({video['duration']}s) from r/{video['subreddit']}")
    
    print(f"\n📂 Videos saved to: data/videos/")
    print(f"📋 Database file: data/db.sqlite")
    print(f"📜 Logs available in: data/logs/")
    
    print(f"\n🎉 Integration example completed!")

def show_database_stats():
    """Show detailed database statistics"""
    
    print(f"\n📊 Detailed Database Statistics")
    print("-" * 35)
    
    db = DatabaseHandler()
    
    # Overall stats
    all_videos = db.get_all_videos()
    total = len(all_videos)
    print(f"Total videos: {total}")
    
    if total > 0:
        # By subreddit
        print(f"\nVideos by subreddit:")
        subreddits = {}
        for video in all_videos:
            subreddit = video.get('subreddit', 'unknown')
            subreddits[subreddit] = subreddits.get(subreddit, 0) + 1
        
        for subreddit, count in subreddits.items():
            print(f"  r/{subreddit}: {count}")
        
        # Recent videos
        print(f"\nMost recent videos:")
        recent = db.get_recent(3)
        for video in recent:
            print(f"  • {video['title'][:30]}... ({video['duration']}s)")

if __name__ == "__main__":
    scrape_and_store_example()
    show_database_stats() 