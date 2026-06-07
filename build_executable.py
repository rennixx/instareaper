#!/usr/bin/env python3
"""
Build InstaReaper Windows Executable
"""

import os
import sys
import subprocess
import shutil
import build_config

def check_dependencies():
    """Check if required build dependencies are installed"""
    print("🔍 Checking build dependencies...")
    
    required_packages = [
        'pyinstaller',
        'pillow',
        'PyQt5',
        'instagrapi',
        'selenium',
        'webdriver-manager',
        'opencv-python',
        'yt-dlp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'pyinstaller':
                # Check if pyinstaller command is available
                subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                             check=True, capture_output=True)
            elif package == 'opencv-python':
                __import__('cv2')
            elif package == 'PyQt5':
                __import__('PyQt5.QtCore')
            elif package == 'pillow':
                __import__('PIL')
            else:
                __import__(package.replace('-', '_').lower())
            print(f"✅ {package}")
        except (ImportError, subprocess.CalledProcessError):
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True

def clean_build_dirs():
    """Clean previous build directories"""
    print("🧹 Cleaning previous builds...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ Removed {dir_name}")
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def create_build_files():
    """Create necessary build files"""
    print("📝 Creating build files...")
    
    # Run build config to create spec and version files
    build_config.create_pyinstaller_spec()
    build_config.create_version_file()

def run_pyinstaller():
    """Run PyInstaller to create executable"""
    print("🔨 Building executable with PyInstaller...")
    
    spec_file = build_config.SPEC_FILE
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', spec_file]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def post_build_cleanup():
    """Clean up after build"""
    print("🧹 Post-build cleanup...")
    
    files_to_remove = [
        'version_info.txt',
        build_config.SPEC_FILE
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Removed {file_path}")

def verify_build():
    """Verify the build was successful"""
    print("🔍 Verifying build...")
    
    exe_path = f"dist/{build_config.APP_NAME}.exe"
    
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print(f"✅ Executable created: {exe_path}")
        print(f"📊 File size: {file_size:.1f} MB")
        return True
    else:
        print(f"❌ Executable not found: {exe_path}")
        return False

def create_portable_package():
    """Create a portable package with all necessary files"""
    print("📦 Creating portable package...")
    
    package_dir = f"dist/{build_config.APP_NAME}_Portable"
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy executable
    exe_source = f"dist/{build_config.APP_NAME}.exe"
    exe_dest = f"{package_dir}/{build_config.APP_NAME}.exe"
    shutil.copy2(exe_source, exe_dest)
    
    # Copy assets
    if os.path.exists("assets"):
        shutil.copytree("assets", f"{package_dir}/assets", dirs_exist_ok=True)
    
    # Copy README
    if os.path.exists("README.md"):
        shutil.copy2("README.md", package_dir)
    
    # Create config template
    config_dir = f"{package_dir}/config"
    os.makedirs(config_dir, exist_ok=True)
    
    # Create data directories
    os.makedirs(f"{package_dir}/data/videos", exist_ok=True)
    os.makedirs(f"{package_dir}/data/logs", exist_ok=True)
    
    print(f"✅ Portable package created: {package_dir}")

def main():
    """Main build process"""
    print("🏗️  Building InstaReaper Windows Application")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Build failed: Missing dependencies")
        return False
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create build files
    create_build_files()
    
    # Run PyInstaller
    if not run_pyinstaller():
        print("❌ Build failed: PyInstaller error")
        return False
    
    # Verify build
    if not verify_build():
        print("❌ Build failed: Verification error")
        return False
    
    # Create portable package
    create_portable_package()
    
    # Cleanup
    post_build_cleanup()
    
    print("\n🎉 Build completed successfully!")
    print(f"📁 Executable: dist/{build_config.APP_NAME}.exe")
    print(f"📦 Portable package: dist/{build_config.APP_NAME}_Portable/")
    print("\n📋 Next step: Run 'python create_installer.py' to create Windows installer")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
