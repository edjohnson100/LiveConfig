import adsk.core, adsk.fusion, traceback
import json
import re
import os

ATTRIBUTE_GROUP = "EdJ_Data"
ATTRIBUTE_NAME = "Config_Snapshots"
ACTIVE_CONFIG_ATTR = "Last_Active_Config"

def _read_manifest_version():
    manifest_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'LiveConfig.manifest')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('version', '')
    except Exception:
        return ''

ADDIN_VERSION = _read_manifest_version()

# Host-side store for user-imported themes -- separate from the built-in
# Light/Dark/Sepia themes baked into style.css. Per-machine, gitignored
# (same pattern as LiveUtilities/GridfinityGeneratorPlus's imported_themes.json):
# survives a restart or a localStorage wipe.
IMPORTED_THEMES_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'imported_themes.json')

def load_imported_themes():
    if not os.path.exists(IMPORTED_THEMES_PATH):
        return {}
    try:
        with open(IMPORTED_THEMES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_imported_theme(theme_id, theme_vars):
    themes = load_imported_themes()
    themes[theme_id] = theme_vars
    with open(IMPORTED_THEMES_PATH, 'w', encoding='utf-8') as f:
        json.dump(themes, f, indent=2)

def delete_imported_theme(theme_id):
    themes = load_imported_themes()
    if theme_id in themes:
        del themes[theme_id]
        with open(IMPORTED_THEMES_PATH, 'w', encoding='utf-8') as f:
            json.dump(themes, f, indent=2)

def clear_imported_themes():
    """Used by Factory Reset Theme Cache -- wipes every host-persisted
    imported theme, not just localStorage, so a reset actually resets."""
    if os.path.exists(IMPORTED_THEMES_PATH):
        os.remove(IMPORTED_THEMES_PATH)

def _themes_dialog_dir():
    root = os.path.dirname(os.path.realpath(__file__))
    themes_dir = os.path.join(root, 'resources', 'themes')
    return themes_dir if os.path.isdir(themes_dir) else os.path.join(root, 'resources')

def export_theme_logic(content, default_name):
    app = adsk.core.Application.get()
    ui = app.userInterface
    fileDialog = ui.createFileDialog()
    fileDialog.title = 'Export Theme'
    fileDialog.filter = 'JSON Files (*.json);;All Files (*.*)'
    fileDialog.initialDirectory = _themes_dialog_dir()
    fileDialog.initialFilename = default_name
    if fileDialog.showSave() == adsk.core.DialogResults.DialogOK:
        try:
            with open(fileDialog.filename, 'w', encoding='utf-8') as f:
                f.write(content)
            ui.messageBox(f'Theme exported to {fileDialog.filename}')
        except Exception as e:
            ui.messageBox(f'Failed to save theme:\n{str(e)}')

# General-purpose host-side settings file (palette geometry, and anything
# else added later). Per-machine, gitignored -- separate from
# imported_themes.json, which is theme-import-specific.
CONFIG_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')

def _load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

def _save_config(updates):
    config_data = _load_config()
    config_data.update(updates)
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except OSError:
        pass

def _save_palette_geometry(palette):
    # Fusion's Palette has no resize/move event -- width/height/left/top/
    # dockingState are only readable on demand, so this is called at the two
    # points the palette's lifecycle actually gives us: the user closing it
    # and the add-in being stopped (right before palette.deleteMe()).
    try:
        _save_config({'palette_geometry': {
            'width': palette.width,
            'height': palette.height,
            'left': palette.left,
            'top': palette.top,
            'docking_state': int(palette.dockingState),
        }})
    except RuntimeError:
        pass

def _restore_palette_geometry(palette):
    geometry = _load_config().get('palette_geometry', {})
    try:
        if 'left' in geometry:
            palette.left = geometry['left']
        if 'top' in geometry:
            palette.top = geometry['top']
        if 'docking_state' in geometry:
            palette.dockingState = geometry['docking_state']
    except RuntimeError:
        pass

def import_theme_logic():
    app = adsk.core.Application.get()
    ui = app.userInterface
    fileDialog = ui.createFileDialog()
    fileDialog.title = 'Import Theme'
    fileDialog.filter = 'JSON Files (*.json);;All Files (*.*)'
    fileDialog.initialDirectory = _themes_dialog_dir()
    if fileDialog.showOpen() == adsk.core.DialogResults.DialogOK:
        try:
            with open(fileDialog.filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            ui.messageBox(f'Failed to read theme:\n{str(e)}')
    return None

def scan_model():
    """Scans parameters and timeline features/groups."""
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return json.dumps({"error": "No design", "addin_version": ADDIN_VERSION, "imported_themes": load_imported_themes()})

    raw_name = app.activeDocument.name
    clean_name = re.sub(r'\s+v\d+$', '', raw_name)

    # 1. Parameters (Safe for Text/Boolean)
    param_data = []
    for param in design.userParameters:
        safe_val = 0
        try:
            # Try to get numeric value
            safe_val = param.value
        except:
            # Fallback for Text/Boolean parameters that crash on .value
            pass

        param_data.append({
            "name": param.name,
            "expression": param.expression,
            "value": safe_val, 
            "unit": param.unit,
            "isFavorite": getattr(param, "isFavorite", False)
        })

    # 2. Timeline Features (Root Features & Groups)
    feature_data = []
    root = design.rootComponent
    
    # A. Root Features
    for feature in root.features:
        if feature.name.startswith("CFG_"):
            feature_data.append({
                "name": feature.name,
                "isSuppressed": feature.isSuppressed
            })
            
    # B. Timeline Groups
    timeline = design.timeline
    for group in timeline.timelineGroups:
        if group.name.startswith("CFG_"):
            feature_data.append({
                "name": group.name,
                "isSuppressed": group.isSuppressed
            })

    # 3. Saved Snapshots
    saved_configs = {}
    attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ATTRIBUTE_NAME)
    if attr:
        try:
            saved_configs = json.loads(attr.value)
        except:
            saved_configs = {}

    last_active = ""
    active_attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ACTIVE_CONFIG_ATTR)
    if active_attr:
        last_active = active_attr.value

    return json.dumps({
        "doc_name": clean_name,
        "parameters": param_data,
        "features": feature_data,
        "configs": saved_configs,
        "active_config": last_active,
        "addin_version": ADDIN_VERSION,
        "imported_themes": load_imported_themes()
    })

def update_parameter(name, expression):
    app = adsk.core.Application.get()
    design = app.activeProduct
    param = design.userParameters.itemByName(name)
    if param:
        try:
            param.expression = str(expression)
        except:
            pass 

def toggle_favorite(name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    param = design.userParameters.itemByName(name)
    if param:
        try:
            current_state = getattr(param, "isFavorite", False)
            param.isFavorite = not current_state
        except:
            pass
    return scan_model()

def toggle_feature(name, should_suppress):
    app = adsk.core.Application.get()
    design = app.activeProduct
    root = design.rootComponent
    
    item = root.features.itemByName(name)
    if not item:
        timeline = design.timeline
        for group in timeline.timelineGroups:
            if group.name == name:
                item = group
                break
        
    if item:
        item.isSuppressed = should_suppress
        adsk.doEvents() 
        
    return scan_model()

def save_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return False
    
    root = design.rootComponent 

    # 1. Parameters
    params = {p.name: p.expression for p in design.userParameters}
    
    # 2. Features
    feats = {}
    for f in root.features:
        if f.name.startswith("CFG_"):
            feats[f.name] = f.isSuppressed
    timeline = design.timeline
    for g in timeline.timelineGroups:
        if g.name.startswith("CFG_"):
            feats[g.name] = g.isSuppressed

    # Load & Update
    current_data = {}
    attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ATTRIBUTE_NAME)
    if attr:
        try:
            current_data = json.loads(attr.value)
        except:
            current_data = {}
    
    current_data[config_name] = {
        "params": params,
        "features": feats
    }

    root.attributes.add(ATTRIBUTE_GROUP, ATTRIBUTE_NAME, json.dumps(current_data))
    root.attributes.add(ATTRIBUTE_GROUP, ACTIVE_CONFIG_ATTR, config_name)
    return True

def delete_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return False
    
    root = design.rootComponent 
    attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ATTRIBUTE_NAME)
    if not attr: return False
    
    try:
        current_data = json.loads(attr.value)
        if config_name in current_data:
            del current_data[config_name]
            root.attributes.add(ATTRIBUTE_GROUP, ATTRIBUTE_NAME, json.dumps(current_data))
            
            active_attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ACTIVE_CONFIG_ATTR)
            if active_attr and active_attr.value == config_name:
                root.attributes.add(ATTRIBUTE_GROUP, ACTIVE_CONFIG_ATTR, "")
            return True
    except:
        pass
    return False

def apply_snapshot(config_name):
    app = adsk.core.Application.get()
    design = app.activeProduct
    root = design.rootComponent 
    
    attr = root.attributes.itemByName(ATTRIBUTE_GROUP, ATTRIBUTE_NAME)
    if not attr: return
    
    data = json.loads(attr.value)
    if config_name not in data: return
    
    snapshot = data[config_name]
    
    design.isComputeDeferred = True
    try:
        # 1. Apply Parameters
        saved_params = snapshot.get("params", {})
        for name, expr in saved_params.items():
            p = design.userParameters.itemByName(name)
            if p: p.expression = expr
            
        # 2. Apply Timeline Features
        saved_feats = snapshot.get("features", {})
        timeline = design.timeline
        for name, is_suppressed in saved_feats.items():
            item = root.features.itemByName(name)
            if not item:
                for group in timeline.timelineGroups:
                    if group.name == name:
                        item = group
                        break
            if item: 
                item.isSuppressed = is_suppressed

        root.attributes.add(ATTRIBUTE_GROUP, ACTIVE_CONFIG_ATTR, config_name)
    except:
        pass
    finally:
        design.isComputeDeferred = False
        app.activeViewport.refresh()