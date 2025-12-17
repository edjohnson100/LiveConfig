import adsk.core, adsk.fusion, traceback
import json
import re

ATTRIBUTE_GROUP = "EdJ_Data"
ATTRIBUTE_NAME = "Config_Snapshots"
ACTIVE_CONFIG_ATTR = "Last_Active_Config"

def scan_model():
    """Scans parameters and timeline features/groups."""
    app = adsk.core.Application.get()
    design = app.activeProduct
    if not design: return json.dumps({"error": "No design"})

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
        "active_config": last_active
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