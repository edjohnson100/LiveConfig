[Setup]
; ==============================================================================
; 📝 CONFIGURATION: EDIT THESE LINES FOR EACH PROJECT
; ==============================================================================

; ⭐️ DEFINE VARIABLES: Change these values for each project ⭐️
; 1. APP_NAME: The descriptive name used in Windows menus and Group names (e.g., "My Fusion Utility").
#define APP_NAME "LiveConfig"
; 2. APP_FOLDER: The physical folder name placed inside the Fusion API directory (e.g., "MyUtilityFolder"). Must be unique and generally avoid spaces.
#define APP_FOLDER "LiveConfig"
; 3. APP_TYPE: The type of Fusion asset. Must exactly match the folder name in Fusion API.
; Options are "Scripts" or "AddIns"
#define APP_TYPE "AddIns" 
; 4. AppVersion: Edit to match the current build
AppVersion=1.0.1
; ==============================================================================
; 📝 END CONFIGURATION
; ==============================================================================

AppName={#APP_NAME}
DefaultGroupName={#APP_NAME}

; --- SINGLE PATH SETTING USING VARIABLES ---
; This works for both Scripts and Add-Ins by substituting APP_TYPE and APP_FOLDER
DefaultDirName={userappdata}\Autodesk\Autodesk Fusion 360\API\{#APP_TYPE}\{#APP_FOLDER}

; The Output Filename
OutputBaseFilename={#APP_NAME}Installer_Win
;
; LICENSE: Looks in the resources folder in the parent directory
LicenseFile=..\resources\License.rtf
;==============================================================================

PrivilegesRequired=lowest
Compression=lzma
SolidCompression=yes
OutputDir=.

[Files]
; ==============================================================================
; SOURCE FILES
; ==============================================================================
;
; ".." means "The Parent Directory" (The Root of your Repo)
; We EXCLUDE the 'Installers' folder, .git, and VSCode settings.
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "Installers,.git,.gitignore,.vscode,__pycache__"

[Icons]
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"