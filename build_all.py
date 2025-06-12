#!/usr/bin/env python3
"""
Master Build Script for InstaReaper Windows Application
"""

import os
import sys
import subprocess
import time

def run_step(step_name, script_name):
    """Run a build step and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔧 {step_name}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"✅ {step_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {step_name} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_name}")
        return False

def install_build_dependencies():
    """Install required build dependencies"""
    print("📦 Installing build dependencies...")
    
    dependencies = [
        'pyinstaller',
        'pillow',
    ]
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_').lower())
            print(f"✅ {dep} already installed")
        except ImportError:
            print(f"📥 Installing {dep}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], check=True)
                print(f"✅ {dep} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {dep}")
                return False
    
    return True

def main():
    """Main build process"""
    print("🏗️  InstaReaper Windows Application Builder")
    print("=" * 60)
    print("This script will build a complete Windows installer for InstaReaper")
    print("including executable, assets, and installer package.")
    print()
    
    start_time = time.time()
    
    # Step 1: Install build dependencies
    if not install_build_dependencies():
        print("❌ Failed to install build dependencies")
        return False
    
    # Step 2: Create assets
    if not run_step("Creating Assets", "create_assets.py"):
        print("❌ Build failed at asset creation")
        return False
    
    # Step 3: Build configuration
    if not run_step("Build Configuration", "build_config.py"):
        print("❌ Build failed at configuration")
        return False
    
    # Step 4: Build executable
    if not run_step("Building Executable", "build_executable.py"):
        print("❌ Build failed at executable creation")
        return False
    
    # Step 5: Create installer
    if not run_step("Creating Installer", "create_installer.py"):
        print("⚠️  Installer creation had issues, but executable is ready")
    
    # Calculate build time
    build_time = time.time() - start_time
    minutes = int(build_time // 60)
    seconds = int(build_time % 60)
    
    print(f"\n{'='*60}")
    print("🎉 BUILD COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"⏱️  Total build time: {minutes}m {seconds}s")
    print()
    print("📁 Output files:")
    print(f"   • Executable: dist/InstaReaper.exe")
    print(f"   • Portable: dist/InstaReaper_Portable/")
    print(f"   • Installer: dist/installer/")
    print()
    print("🚀 Your InstaReaper Windows application is ready!")
    print("   You can now distribute the installer or portable version.")
    print()
    print("📋 Next steps:")
    print("   1. Test the executable: dist/InstaReaper.exe")
    print("   2. Run the installer to test installation")
    print("   3. Share with users!")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 Build completed successfully!")
        input("Press Enter to exit...")
    else:
        print("\n❌ Build failed!")
        input("Press Enter to exit...")
    
    sys.exit(0 if success else 1) 