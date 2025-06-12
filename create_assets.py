#!/usr/bin/env python3
"""
Create Assets for InstaReaper Windows Application
"""

import os
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

def create_directories():
    """Create necessary directories"""
    os.makedirs("assets", exist_ok=True)
    print("✅ Created assets directory")

def create_app_icon():
    """Create application icon"""
    # Create a 256x256 icon
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background gradient (Instagram-like)
    for y in range(size):
        # Gradient from purple to orange
        r = int(131 + (255 - 131) * (y / size))  # 131 -> 255
        g = int(58 + (87 - 58) * (y / size))    # 58 -> 87
        b = int(180 + (51 - 180) * (y / size))  # 180 -> 51
        
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # Draw main icon elements
    center = size // 2
    
    # Outer circle (camera body)
    circle_radius = size // 3
    draw.ellipse([
        center - circle_radius, center - circle_radius,
        center + circle_radius, center + circle_radius
    ], outline=(255, 255, 255, 255), width=8)
    
    # Inner circle (lens)
    inner_radius = circle_radius // 2
    draw.ellipse([
        center - inner_radius, center - inner_radius,
        center + inner_radius, center + inner_radius
    ], outline=(255, 255, 255, 255), width=6)
    
    # Flash dot
    flash_x = center + circle_radius // 2
    flash_y = center - circle_radius // 2
    draw.ellipse([
        flash_x - 8, flash_y - 8,
        flash_x + 8, flash_y + 8
    ], fill=(255, 255, 255, 255))
    
    # Add "R" for Reddit integration
    try:
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "R" in bottom right
    r_x = center + circle_radius // 3
    r_y = center + circle_radius // 3
    draw.text((r_x, r_y), "R", fill=(255, 255, 255, 255), font=font, anchor="mm")
    
    # Save as ICO file
    icon_path = "assets/icon.ico"
    
    # Create multiple sizes for ICO
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for ico_size in sizes:
        resized = img.resize((ico_size, ico_size), Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as ICO
    images[0].save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])
    print(f"✅ Created application icon: {icon_path}")
    
    # Also save as PNG for other uses
    img.save("assets/icon.png", format='PNG')
    print("✅ Created PNG icon: assets/icon.png")

def create_splash_screen():
    """Create splash screen image"""
    width, height = 400, 300
    img = Image.new('RGB', (width, height), (45, 45, 45))
    draw = ImageDraw.Draw(img)
    
    # Background gradient
    for y in range(height):
        # Dark gradient
        intensity = int(45 + 20 * (y / height))
        draw.line([(0, y), (width, y)], fill=(intensity, intensity, intensity))
    
    # App name
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        subtitle_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Title
    title = "InstaReaper"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = height // 2 - 40
    
    draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)
    
    # Subtitle
    subtitle = "Reddit to Instagram Content Pipeline"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + 50
    
    draw.text((subtitle_x, subtitle_y), subtitle, fill=(200, 200, 200), font=subtitle_font)
    
    # Version
    version = "v1.0.0"
    version_bbox = draw.textbbox((0, 0), version, font=subtitle_font)
    version_width = version_bbox[2] - version_bbox[0]
    version_x = (width - version_width) // 2
    version_y = subtitle_y + 30
    
    draw.text((version_x, version_y), version, fill=(150, 150, 150), font=subtitle_font)
    
    # Save splash screen
    splash_path = "assets/splash.png"
    img.save(splash_path, format='PNG')
    print(f"✅ Created splash screen: {splash_path}")

def create_readme():
    """Create a proper README for the built application"""
    readme_content = """# InstaReaper - Windows Application

## Overview
InstaReaper is an automated content pipeline that scrapes videos from Reddit and posts them to Instagram as Reels.

## Features
- 🎥 Reddit video scraping with audio
- 📱 Instagram posting automation
- 🌐 Web-based Instagram authentication
- 🎨 Modern dark theme GUI
- ⏰ Smart rate limiting and scheduling
- 📊 Upload tracking and statistics

## Installation
1. Run the InstaReaper installer
2. Launch the application from Start Menu or Desktop
3. Follow the setup wizard

## First Time Setup
1. **Instagram Authentication**: Click "🌐 Setup Instagram Login" to authenticate via web browser
2. **Reddit Configuration**: The app comes pre-configured with popular subreddits
3. **Download Videos**: Click "Scrape Videos" to download content from Reddit
4. **Post to Instagram**: Select videos and click "Post to Instagram"

## Important Notes
- **Rate Limiting**: The app automatically limits uploads to prevent Instagram restrictions
- **Daily Limits**: Maximum 3 posts per day with 30+ minute intervals
- **Manual Usage**: Use Instagram manually between automated posts for best results
- **Session Persistence**: Your login session is saved securely

## File Locations
- **Configuration**: `%APPDATA%\\InstaReaper\\config\\`
- **Videos**: `%APPDATA%\\InstaReaper\\data\\videos\\`
- **Logs**: `%APPDATA%\\InstaReaper\\data\\logs\\`

## Troubleshooting
- **Instagram Restrictions**: If you get activity restrictions, use Instagram manually for 24-48 hours
- **Login Issues**: Clear sessions and re-authenticate via web browser
- **Video Issues**: Ensure videos are under 60 seconds for Instagram compatibility

## Support
For support and updates, visit: https://github.com/instareaper/instareaper

## Version
1.0.0 - Initial Release

---
© 2024 InstaReaper Team
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ Created README.md")

def main():
    """Create all assets"""
    print("🎨 Creating InstaReaper Assets")
    print("=" * 35)
    
    create_directories()
    create_app_icon()
    create_splash_screen()
    create_readme()
    
    print("\n✅ All assets created successfully!")
    print("\n📋 Next step: Run 'python build_executable.py'")

if __name__ == "__main__":
    main() 