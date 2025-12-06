[Setup]
; ==============================================================================
; 📝 CONFIGURATION: EDIT THESE LINES FOR EACH PROJECT
; ==============================================================================
AppName=My Addin Name
AppVersion=1.0.0
DefaultGroupName=MyAddinName
;
; EDIT: The folder name created in %APPDATA%. 
; Usually matches your Repo Name.
DefaultDirName={userappdata}\Autodesk\Autodesk Fusion 360\API\AddIns\MyAddinFolderName
;
; EDIT: The Output Filename
OutputBaseFilename=MyAddinInstaller_Win
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
; ".." means "The Parent Directory" (The Root of your Repo)
; We EXCLUDE the 'Installers' folder, .git, and VSCode settings.
Source: "..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "Installers,.git,.gitignore,.vscode,__pycache__"

[Icons]
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"