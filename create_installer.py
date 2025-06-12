#!/usr/bin/env python3
"""
Create Windows Installer for InstaReaper
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import build_config

def create_inno_setup_script():
    """Create Inno Setup script for Windows installer"""
    print("📝 Creating Inno Setup script...")
    
    # Get current directory
    source_dir = os.path.abspath(".")
    
    inno_script = f'''[Setup]
AppId={{{{B8E5F8A1-2C3D-4E5F-6789-ABCDEF123456}}}}
AppName={build_config.APP_NAME}
AppVersion={build_config.APP_VERSION}
AppVerName={build_config.APP_NAME} {build_config.APP_VERSION}
AppPublisher={build_config.APP_AUTHOR}
AppPublisherURL=https://github.com/instareaper/instareaper
AppSupportURL=https://github.com/instareaper/instareaper
AppUpdatesURL=https://github.com/instareaper/instareaper
DefaultDirName={{autopf}}\\{build_config.APP_NAME}
DefaultGroupName={build_config.APP_NAME}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=dist\\installer
OutputBaseFilename={build_config.APP_NAME}_Setup_v{build_config.APP_VERSION}
SetupIconFile=assets\\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\\{build_config.APP_NAME}.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "assets\\*"; DestDir: "{{app}}\\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{{group}}\\{build_config.APP_NAME}"; Filename: "{{app}}\\{build_config.APP_NAME}.exe"; IconFilename: "{{app}}\\assets\\icon.ico"
Name: "{{group}}\\{{cm:ProgramOnTheWeb,{build_config.APP_NAME}}}"; Filename: "https://github.com/instareaper/instareaper"
Name: "{{group}}\\{{cm:UninstallProgram,{build_config.APP_NAME}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{build_config.APP_NAME}"; Filename: "{{app}}\\{build_config.APP_NAME}.exe"; IconFilename: "{{app}}\\assets\\icon.ico"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\{build_config.APP_NAME}"; Filename: "{{app}}\\{build_config.APP_NAME}.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\{build_config.APP_NAME}.exe"; Description: "{{cm:LaunchProgram,{build_config.APP_NAME}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{userappdata}}\\{build_config.APP_NAME}"

[Code]
procedure InitializeWizard;
begin
  WizardForm.LicenseAcceptedRadio.Checked := True;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsDotNetInstalled(net48, 0) then begin
    MsgBox('This application requires Microsoft .NET Framework 4.8 or later.', mbInformation, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
begin
  if CurStep = ssPostInstall then begin
    // Create application data directory
    AppDataDir := ExpandConstant('{{userappdata}}\\{build_config.APP_NAME}');
    ForceDirectories(AppDataDir);
    ForceDirectories(AppDataDir + '\\data\\videos');
    ForceDirectories(AppDataDir + '\\data\\logs');
    ForceDirectories(AppDataDir + '\\config');
  end;
end;
'''
    
    # Save Inno Setup script
    script_path = f"{build_config.APP_NAME}_installer.iss"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(inno_script)
    
    print(f"✅ Created Inno Setup script: {script_path}")
    return script_path

def find_inno_setup():
    """Find Inno Setup compiler"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def compile_installer(script_path):
    """Compile the installer using Inno Setup"""
    print("🔨 Compiling Windows installer...")
    
    # Find Inno Setup compiler
    iscc_path = find_inno_setup()
    
    if not iscc_path:
        print("❌ Inno Setup not found!")
        print("Please install Inno Setup from: https://jrsoftware.org/isinfo.php")
        print("Then run this script again.")
        return False
    
    print(f"✅ Found Inno Setup: {iscc_path}")
    
    # Create output directory
    os.makedirs("dist/installer", exist_ok=True)
    
    # Compile installer
    cmd = [iscc_path, script_path]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Installer compiled successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installer compilation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def create_nsis_installer():
    """Alternative: Create NSIS installer script"""
    print("📝 Creating NSIS installer script (alternative)...")
    
    nsis_script = f'''!define APPNAME "{build_config.APP_NAME}"
!define APPVERSION "{build_config.APP_VERSION}"
!define APPNAMEANDVERSION "${{APPNAME}} ${{APPVERSION}}"

Name "${{APPNAMEANDVERSION}}"
OutFile "dist\\installer\\${{APPNAME}}_Setup_v${{APPVERSION}}.exe"
InstallDir "$PROGRAMFILES64\\${{APPNAME}}"
RequestExecutionLevel user

!include MUI2.nsh

!define MUI_ABORTWARNING
!define MUI_ICON "assets\\icon.ico"
!define MUI_UNICON "assets\\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\{build_config.APP_NAME}.exe"
    File /r "assets"
    File "README.md"
    
    CreateDirectory "$APPDATA\\${{APPNAME}}"
    CreateDirectory "$APPDATA\\${{APPNAME}}\\data\\videos"
    CreateDirectory "$APPDATA\\${{APPNAME}}\\data\\logs"
    CreateDirectory "$APPDATA\\${{APPNAME}}\\config"
    
    CreateShortcut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\{build_config.APP_NAME}.exe"
    CreateShortcut "$SMPROGRAMS\\${{APPNAME}}.lnk" "$INSTDIR\\{build_config.APP_NAME}.exe"
    
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\{build_config.APP_NAME}.exe"
    Delete "$INSTDIR\\README.md"
    RMDir /r "$INSTDIR\\assets"
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$DESKTOP\\${{APPNAME}}.lnk"
    Delete "$SMPROGRAMS\\${{APPNAME}}.lnk"
    
    RMDir /r "$APPDATA\\${{APPNAME}}"
SectionEnd
'''
    
    nsis_path = f"{build_config.APP_NAME}_installer.nsi"
    with open(nsis_path, 'w', encoding='utf-8') as f:
        f.write(nsis_script)
    
    print(f"✅ Created NSIS script: {nsis_path}")
    return nsis_path

def create_batch_installer():
    """Create a simple batch file installer as fallback"""
    print("📝 Creating batch installer (fallback)...")
    
    batch_content = f'''@echo off
echo Installing {build_config.APP_NAME} v{build_config.APP_VERSION}
echo.

set "INSTALL_DIR=%PROGRAMFILES%\\{build_config.APP_NAME}"
set "APP_DATA=%APPDATA%\\{build_config.APP_NAME}"

echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul

echo Copying files...
copy "dist\\{build_config.APP_NAME}.exe" "%INSTALL_DIR%\\" >nul
xcopy "assets" "%INSTALL_DIR%\\assets\\" /E /I /Q >nul
copy "README.md" "%INSTALL_DIR%\\" >nul

echo Creating application data directories...
mkdir "%APP_DATA%" 2>nul
mkdir "%APP_DATA%\\data\\videos" 2>nul
mkdir "%APP_DATA%\\data\\logs" 2>nul
mkdir "%APP_DATA%\\config" 2>nul

echo Creating shortcuts...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{build_config.APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{build_config.APP_NAME}.exe'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo You can now run {build_config.APP_NAME} from your Desktop or Start Menu.
echo.
pause
'''
    
    batch_path = f"dist/installer/{build_config.APP_NAME}_Install.bat"
    os.makedirs("dist/installer", exist_ok=True)
    
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print(f"✅ Created batch installer: {batch_path}")

def main():
    """Main installer creation process"""
    print("📦 Creating Windows Installer for InstaReaper")
    print("=" * 50)
    
    # Check if executable exists
    exe_path = f"dist/{build_config.APP_NAME}.exe"
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found: {exe_path}")
        print("Please run 'python build_executable.py' first")
        return False
    
    # Create Inno Setup script
    inno_script = create_inno_setup_script()
    
    # Try to compile with Inno Setup
    if compile_installer(inno_script):
        installer_path = f"dist/installer/{build_config.APP_NAME}_Setup_v{build_config.APP_VERSION}.exe"
        if os.path.exists(installer_path):
            file_size = os.path.getsize(installer_path) / (1024 * 1024)  # MB
            print(f"✅ Windows installer created: {installer_path}")
            print(f"📊 Installer size: {file_size:.1f} MB")
        
        # Clean up script
        os.remove(inno_script)
    else:
        print("⚠️  Inno Setup compilation failed, creating alternatives...")
        
        # Create NSIS script as alternative
        nsis_script = create_nsis_installer()
        print(f"💡 You can compile the NSIS script manually with NSIS")
        
        # Create batch installer as fallback
        create_batch_installer()
    
    print("\n🎉 Installer creation completed!")
    print("\n📋 Distribution files:")
    print(f"• Executable: dist/{build_config.APP_NAME}.exe")
    print(f"• Portable: dist/{build_config.APP_NAME}_Portable/")
    print(f"• Installer: dist/installer/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 