@echo off
TITLE Fusion Add-In Master Builder
CLS

:: ==============================================================================
:: 📝 CONFIGURATION
:: ==============================================================================
:: Path to Inno Setup Compiler
SET "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

:: * Define the Application Name for Installer Filenames ⭐️
SET "APP_NAME=LiveConfig" 
:: ==============================================================================

ECHO ==========================================
ECHO      FUSION 360 ADD-IN MASTER BUILDER
ECHO ==========================================

:: CHECK FOR PARENT MANIFEST TO ENSURE WE ARE IN THE RIGHT PLACE
IF NOT EXIST "..\*.manifest" (
    ECHO [ERROR] Could not find a .manifest file in the parent folder.
    ECHO Please ensure this 'Installers' folder is inside your Add-In root directory.
    PAUSE
    EXIT /B
)

:: --- PART 1: BUILD EXE ---
ECHO [1/2] Building EXE Installer...
"%ISCC%" "build_exe.iss" /Q
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Inno Setup compilation failed!
    PAUSE
    EXIT /B
)
ECHO     - EXE Build Complete.

:: --- PART 2: BUILD MSI ---
ECHO [2/2] Building MSI Installer...

:: 1. Cleanup old artifacts
IF EXIST *.wixobj DEL *.wixobj
IF EXIST installer.wxs DEL installer.wxs

:: 2. Run Python Generator
python build_wix.py
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Python generation failed.
    PAUSE
    EXIT /B
)

:: 3. Compile (Candle)
candle installer.wxs -nologo
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Candle - WiX failed.
    PAUSE
    EXIT /B
)

:: 4. Link (Light) -> Output MSI to THIS folder
:: NOTE: The output file name is now dynamically set using the APP_NAME variable!
light -ext WixUIExtension -out "%APP_NAME%Installer_Win.msi" installer.wixobj -sice:ICE64 -sice:ICE91 -sw1032 -nologo
IF %ERRORLEVEL% NEQ 0 (
    ECHO [ERROR] Light - WiX failed.
    PAUSE
    EXIT /B
)

:: 5. Cleanup Temp Files
DEL *.wixobj
DEL installer.wxs

ECHO     - MSI Build Complete.
ECHO.
ECHO ==========================================
ECHO           ALL BUILDS SUCCESSFUL!
ECHO ==========================================
PAUSE