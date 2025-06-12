#!/usr/bin/env python3
"""
Test script for RedditScraper
Demonstrates usage of the scraper module
"""

import sys
import os

# Add current directory to path so we can import our modules
sys.path.append('.')

from scraper.reddit_scraper import RedditScraper

def test_scraper():
    """Test the Reddit scraper functionality"""
    
    print("🔥 InstaReaper Reddit Scraper Test")
    print("=" * 40)
    
    # Initialize scraper
    scraper = RedditScraper()
    
    # Test subreddits
    test_subreddits = ['memes', 'funny', 'dankmemes']
    
    for subreddit in test_subreddits:
        print(f"\n📡 Testing scraper for r/{subreddit}")
        print("-" * 30)
        
        # Check existing downloads
        existing_count = scraper.get_downloaded_by_subreddit(subreddit)
        print(f"Existing downloads for r/{subreddit}: {existing_count}")
        
        try:
            # Scrape videos (limit to 3 for testing)
            videos = scraper.scrape(subreddit, limit=3)
            
            print(f"✅ Found {len(videos)} new videos from r/{subreddit}")
            
            # Display results
            for i, video in enumerate(videos, 1):
                print(f"\n  Video {i}:")
                print(f"    Title: {video['title'][:50]}...")
                print(f"    Duration: {video['duration']}s")
                print(f"    Filename: {video['filename']}")
                print(f"    URL: {video['url']}")
                
        except Exception as e:
            print(f"❌ Error testing r/{subreddit}: {e}")
    
    # Overall statistics
    total_downloads = scraper.get_downloaded_count()
    print(f"\n📊 Total videos downloaded: {total_downloads}")
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    test_scraper() 