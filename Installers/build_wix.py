import os
import uuid

# ==============================================================================
# 📝 CONFIGURATION: EDIT THESE 3 LINES FOR EACH PROJECT
# ==============================================================================
APP_NAME = "My Addin Name"               
MANUFACTURER = "My Brand Name"           
# IMPORTANT: Generate a NEW GUID for every NEW app.
PRODUCT_UPGRADE_CODE = "PUT-NEW-GUID-HERE" 
# ==============================================================================

# IGNORE LIST (Added 'Installers' to prevent recursion)
IGNORE_LIST = [
    "installer.wxs", "installer.wixobj", ".msi", ".git", ".gitignore", 
    "build_wix.py", "__pycache__", ".vscode", ".DS_Store", ".pdb", 
    ".bat", ".iss", "build_exe.iss", "Installers"
]

def get_guid():
    return str(uuid.uuid4()).upper()

def sanitize_id(path_string):
    """Turns a path into a valid WiX ID"""
    clean = path_string.replace("\\", "_").replace("/", "_")
    clean = "".join(c if c.isalnum() else "_" for c in clean)
    if clean[0].isdigit():
        clean = "_" + clean
    return clean[-65:]

def main():
    # SET ROOT TO PARENT DIRECTORY
    script_dir = os.getcwd()
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    folder_name = os.path.basename(root_dir)
    
    component_refs = []
    
    # Registry Key Base
    reg_key_path = f"Software\\{MANUFACTURER.replace(' ', '')}\\{APP_NAME.replace(' ', '')}"
    
    def recurse(path):
        inner_xml = []
        try:
            items = os.listdir(path)
        except OSError:
            return ""
            
        for item in items:
            full_path = os.path.join(path, item)
            rel_path = os.path.relpath(full_path, start=script_dir) # Relative to build script for Source path

            if item in IGNORE_LIST or item.endswith((".msi", ".wixobj", ".wxs")):
                continue
                
            if os.path.isdir(full_path):
                folder_id = f"DIR_{sanitize_id(rel_path)}"
                inner_xml.append(f'<Directory Id="{folder_id}" Name="{item}">')
                inner_xml.append(recurse(full_path))
                inner_xml.append('</Directory>')
            else:
                safe_name = sanitize_id(rel_path)
                rand_suffix = get_guid().replace("-", "")[:5] 
                
                comp_id = f"COMP_{safe_name}_{rand_suffix}"
                file_id = f"FILE_{safe_name}_{rand_suffix}"
                
                component_refs.append(f'<ComponentRef Id="{comp_id}" />')
                
                inner_xml.append(f'<Component Id="{comp_id}" Guid="{get_guid()}">')
                inner_xml.append(f'<RegistryValue Root="HKCU" Key="{reg_key_path}" Name="{safe_name}" Type="string" Value="1" KeyPath="yes" />')
                # Source needs to point up one level then down
                inner_xml.append(f'<File Id="{file_id}" Source="{rel_path}" />')
                inner_xml.append('</Component>')
        return "\n".join(inner_xml)

    print(f"Scanning directory: {root_dir}...")
    dir_xml = recurse(root_dir)
    refs_xml = "\n".join(component_refs)
    
    final_output = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="{APP_NAME}" Language="1033" Version="1.0.0.0" Manufacturer="{MANUFACTURER}" UpgradeCode="{PRODUCT_UPGRADE_CODE}">
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perUser" />
    <MediaTemplate EmbedCab="yes" />

    <UIRef Id="WixUI_Minimal" />
    <WixVariable Id="WixUILicenseRtf" Value="..\\resources\\License.rtf" />
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="AppDataFolder">
        <Directory Id="Autodesk" Name="Autodesk">
           <Directory Id="Fusion360" Name="Autodesk Fusion 360">
             <Directory Id="API" Name="API">
               <Directory Id="AddIns" Name="AddIns">
                 <Directory Id="INSTALLFOLDER" Name="{folder_name}">
                    {dir_xml}
                 </Directory>
               </Directory>
             </Directory>
           </Directory>
        </Directory>
      </Directory>
    </Directory>

    <Feature Id="ProductFeature" Title="Main Feature" Level="1">
      {refs_xml}
    </Feature>
  </Product>
</Wix>
"""
    
    with open("installer.wxs", "w", encoding="utf-8") as f:
        f.write(final_output)
    
    print("Success! 'installer.wxs' generated.")

if __name__ == "__main__":
    main()