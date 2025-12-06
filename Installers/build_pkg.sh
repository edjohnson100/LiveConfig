#!/bin/bash
set -e

# ==============================================================================
# 📝 CONFIGURATION (edit this section)
# ==============================================================================
APP_NAME="My_Addin_Name"                 
IDENTIFIER="com.mybrand.myaddin"         
VERSION="1.0"
# ==============================================================================

# GET PARENT FOLDER NAME
# We assume the script is in /Repo/Installers/
# So ".." is /Repo/
REPO_ROOT=".."
FOLDER_NAME=$(basename "$(cd "$REPO_ROOT" && pwd)")
INSTALL_LOCATION="Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/$FOLDER_NAME"

echo "=========================================="
echo "      MAC USER-ONLY INSTALLER BUILDER"
echo "=========================================="

# 1. CLEANUP OLD BUILDS
rm -f "$APP_NAME.pkg"
rm -f "component.pkg"
rm -f "distribution.xml"
rm -rf "staging_area"

# 2. CREATE STAGING AREA (To exclude 'Installers' folder from the build)
echo "📦 Staging files..."
mkdir -p "staging_area"
# Copy everything from Parent to Staging, excluding specific items
rsync -av --exclude='Installers' --exclude='.git' --exclude='.gitignore' --exclude='.DS_Store' --exclude='__pycache__' "$REPO_ROOT/" "staging_area/"

# 3. PERMISSIONS FIX
echo "🔧 Fixing permissions..."
find "staging_area" -type f -exec chmod 644 {} \;
find "staging_area" -type d -exec chmod 755 {} \;

# 4. BUILD COMPONENT
echo "📦 Building Component..."
pkgbuild --root "staging_area" \
         --identifier "$IDENTIFIER" \
         --version "$VERSION" \
         --install-location "$INSTALL_LOCATION" \
         component.pkg

# 5. GENERATE DISTRIBUTION XML
echo "📝 Generating XML..."
cat <<EOF > distribution.xml
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>$APP_NAME</title>
    <options customize="never" require-scripts="false"/>
    
    <license file="../resources/License.rtf"/>
    
    <domains enable_anywhere="false" enable_currentUserHome="true" enable_localSystem="false" />
    <choices-outline>
        <line choice="default"/>
    </choices-outline>
    <choice id="default" title="$APP_NAME">
        <pkg-ref id="$IDENTIFIER"/>
    </choice>
    <pkg-ref id="$IDENTIFIER" version="$VERSION" onConclusion="none">component.pkg</pkg-ref>
</installer-gui-script>
EOF

# 6. BUILD FINAL INSTALLER
echo "💿 Creating Final Installer..."
productbuild --distribution distribution.xml \
             --package-path . \
             "$APP_NAME.pkg"

# 7. CLEANUP
rm component.pkg
rm distribution.xml
rm -rf "staging_area"

echo "=========================================="
echo "✅ SUCCESS! Installer created: $APP_NAME.pkg"
echo "=========================================="