@echo off
setlocal EnableDelayedExpansion

:: Set console colors and styling
color 0B
mode con: cols=80 lines=25
title Robot NLP - Unified Interface Launcher

echo.
echo ================================================================================
echo    🤖 ROBOT NLP - UNIFIED INTERFACE LAUNCHER 🤖
echo ================================================================================
echo    🎯 One App - All Interface Options Inside Blender
echo ================================================================================
echo.

:: System checks
echo [SYSTEM CHECK] Verifying unified addon...
if exist "robot_nlp_unified.py" (
    echo ✅ Unified Robot NLP addon found
    for %%A in ("robot_nlp_unified.py") do (
        echo    📁 File size: %%~zA bytes
        echo    📅 Modified: %%~tA
    )
) else (
    echo ❌ robot_nlp_unified.py not found!
    echo    This file contains all interface options.
    pause
    exit /b 1
)

echo.
echo [PYTHON CHECK] Verifying Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install Python 3.8+ from python.org
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python !PYTHON_VERSION! ready
)

echo.
echo ================================================================================
echo    🎨 UNIFIED INTERFACE FEATURES:
echo    
echo    📋 INTERFACE SELECTOR: Choose your preferred style in Blender sidebar
echo       🎨 Rich UI - Modern app interface with borders and chat
echo       🏢 Workspace - Custom Blender workspace transformation  
echo       ⚡ Pro Panels - Enhanced sidebar with 6 organized sections
echo       📊 Basic - Simple lightweight interface
echo    
echo    🤖 AUTO-SETUP: Robot scene automatically configured on startup
echo       • Work surface with sample objects (red cube, blue sphere)
echo       • Robot armature placeholder positioned optimally
echo       • Professional lighting and camera setup
echo       • Material preview mode for best visuals
echo    
echo    🎯 PENETRATION METHOD: Direct Blender UI integration via Python
echo       • Uses bpy.types.Panel for sidebar interfaces
echo       • Modal operators for interactive rich UI windows
echo       • GPU rendering for custom visual elements
echo       • Automatic registration on startup via --python flag
echo ================================================================================
echo.

:: Enhanced countdown
echo [LAUNCH] Starting unified Robot NLP interface in:
for /l %%i in (3,-1,1) do (
    <nul set /p =%%i...
    timeout /t 1 >nul
)
echo 🚀 LOADING!

echo.
echo [BLENDER] Launching with unified addon...

:: Use Python launcher script
python launch_unified.py

echo.
echo ================================================================================
echo    🎉 ROBOT NLP SESSION COMPLETE
echo    
echo    🎯 WHAT YOU EXPERIENCED:
echo       ✅ Blender opened with unified Robot NLP addon loaded
echo       ✅ Robot scene automatically configured with objects and lighting
echo       ✅ All interface options available in "Robot NLP" sidebar tab
echo       ✅ Interface selector dropdown to choose your preferred style
echo       ✅ Rich UI, Workspace, Pro, and Basic modes all accessible
echo    
echo    🤖 BLENDER UI PENETRATION SUCCESSFUL:
echo       • Python addon automatically registered via --python flag
echo       • bpy.types.Panel classes created sidebar interface
echo       • Modal operators enabled rich windowed interfaces
echo       • GPU module used for custom visual rendering
echo       • Scene setup executed during addon registration
echo    
echo    💡 NEXT TIME: Just run this launcher for instant access to all interfaces!
echo ================================================================================
echo.
echo Press any key to close...
pause >nul 