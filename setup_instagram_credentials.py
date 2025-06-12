#!/usr/bin/env python3
"""
Instagram Credentials Setup Script

This script helps you securely configure your Instagram credentials for InstaReaper.
"""

import os
import json
import getpass
from pathlib import Path

def setup_instagram_credentials():
    """Setup Instagram credentials interactively"""
    print("🔐 Instagram Credentials Setup for InstaReaper")
    print("=" * 50)
    print()
    
    # Ensure config directory exists
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    credentials_file = config_dir / "credentials.json"
    
    # Check if credentials already exist
    if credentials_file.exists():
        print("⚠️  Credentials file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("❌ Setup cancelled.")
            return False
    
    print("Please enter your Instagram credentials:")
    print("(Your credentials will be stored securely in config/credentials.json)")
    print()
    
    # Get username
    while True:
        username = input("Instagram Username: ").strip()
        if username and username != "your_instagram_username":
            break
        print("❌ Please enter a valid Instagram username")
    
    # Get password securely
    while True:
        password = getpass.getpass("Instagram Password: ").strip()
        if password and password != "your_instagram_password":
            break
        print("❌ Please enter a valid password")
    
    # Create credentials structure
    credentials = {
        "username": username,
        "password": password,
        "session_file": "data/instagram_session.json",
        "device_settings": {
            "device_id": "",
            "uuid": "",
            "phone_id": "",
            "advertising_id": ""
        },
        "notes": [
            "Credentials configured via setup script",
            "Keep this file secure and never commit it to version control",
            "Device settings will be auto-generated on first login"
        ]
    }
    
    try:
        # Save credentials
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=4)
        
        # Set secure file permissions (Windows compatible)
        try:
            os.chmod(credentials_file, 0o600)
        except:
            pass  # Windows doesn't support chmod the same way
        
        print()
        print("✅ Instagram credentials saved successfully!")
        print(f"📁 Saved to: {credentials_file}")
        print()
        print("🔒 Security Notes:")
        print("   • Your credentials are stored locally only")
        print("   • Never share the credentials.json file")
        print("   • The file is excluded from version control")
        print()
        print("🚀 You can now use Instagram posting in InstaReaper!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        return False

def test_credentials():
    """Test the configured credentials"""
    print("\n🧪 Testing Instagram Credentials")
    print("=" * 35)
    
    try:
        from uploader.instagram_poster import InstagramPoster
        
        poster = InstagramPoster()
        
        print("📋 Loading credentials...")
        if not poster.load_credentials():
            print("❌ Failed to load credentials")
            return False
        
        print("🔐 Testing authentication...")
        if poster.authenticate():
            print("✅ Authentication successful!")
            print(f"📱 Logged in as: @{poster.credentials['username']}")
            
            # Get account info
            if poster.client:
                try:
                    user_info = poster.client.account_info()
                    print(f"👤 Account: {user_info.full_name}")
                    
                    # Try different attribute names for follower count
                    try:
                        followers = getattr(user_info, 'follower_count', None) or getattr(user_info, 'followers_count', 0)
                        posts = getattr(user_info, 'media_count', None) or getattr(user_info, 'medias_count', 0)
                        print(f"📊 Followers: {followers:,}")
                        print(f"📝 Posts: {posts:,}")
                    except:
                        print("📊 Account info retrieved (details unavailable)")
                except Exception as e:
                    print(f"⚠️  Could not get account details: {e}")
            
            poster.logout()
            return True
        else:
            print("❌ Authentication failed!")
            print("💡 Please check your username and password")
            return False
            
    except ImportError:
        print("❌ Instagram poster module not available")
        print("💡 Make sure instagrapi is installed: pip install instagrapi")
        return False
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

def main():
    """Main setup function"""
    print("🎯 InstaReaper Instagram Setup")
    print("=" * 30)
    print()
    print("Choose an option:")
    print("1. Setup new credentials")
    print("2. Test existing credentials")
    print("3. Exit")
    print()
    
    while True:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            if setup_instagram_credentials():
                # Offer to test after setup
                test_choice = input("\nWould you like to test the credentials now? (Y/n): ").lower().strip()
                if test_choice != 'n':
                    test_credentials()
            break
            
        elif choice == "2":
            test_credentials()
            break
            
        elif choice == "3":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main() 