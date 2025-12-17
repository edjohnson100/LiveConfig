# LiveConfig.py
# Entry point for the EdJ Configurator
import adsk.core, adsk.fusion, adsk.cam, traceback
import json
import os
import importlib 
from pathlib import Path

# Import our logic module
from . import config_logic

# --- FORCE RELOAD ---
importlib.reload(config_logic)

# Global variables
app = None
ui = None
handlers = []
palette_id = 'EdJ_Config_Palette'
command_id = 'EdJConfigCmd'

class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = args.command
            onExecute = MyCommandExecuteHandler()
            command.execute.add(onExecute)
            handlers.append(onExecute)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # --- PALETTE CREATION LOGIC ---
            palette = ui.palettes.itemById(palette_id)
            
            if not palette:
                cmd_path = Path(__file__).resolve().parent
                html_file = cmd_path / 'resources' / 'html' / 'index.html'
                url = html_file.as_uri()
                
                palette = ui.palettes.add(palette_id, 'LiveConfig', url, True, True, True, 350, 500)
                palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight
                
                onHtmlEvent = MyHTMLEventHandler()
                palette.incomingFromHTML.add(onHtmlEvent)
                handlers.append(onHtmlEvent)
                
                onClose = MyPaletteCloseHandler()
                palette.closed.add(onClose)
                handlers.append(onClose)
            
            palette.isVisible = True

        except:
            if ui:
                ui.messageBox('Command Execution Failed:\n{}'.format(traceback.format_exc()))

class MyHTMLEventHandler(adsk.core.HTMLEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            html_args = adsk.core.HTMLEventArgs.cast(args)
            data = json.loads(html_args.data)
            action = data.get('action')
            
            # --- ROUTING LOGIC ---
            
            if action == 'refresh_data':
                payload = config_logic.scan_model()
                palette = ui.palettes.itemById(palette_id)
                if palette: palette.sendInfoToHTML('update_ui', payload)

            elif action == 'update_param':
                config_logic.update_parameter(data.get('name'), data.get('value'))
            
            elif action == 'toggle_favorite':
                payload = config_logic.toggle_favorite(data.get('name'))
                palette = ui.palettes.itemById(palette_id)
                if palette: palette.sendInfoToHTML('update_ui', payload)
                
            elif action == 'toggle_feature':
                payload = config_logic.toggle_feature(data.get('name'), data.get('is_suppressed'))
                palette = ui.palettes.itemById(palette_id)
                if palette: palette.sendInfoToHTML('update_ui', payload)

            elif action == 'save_snapshot':
                success = config_logic.save_snapshot(data.get('config_name'))
                if success:
                    payload = config_logic.scan_model()
                    palette = ui.palettes.itemById(palette_id)
                    palette.sendInfoToHTML('update_ui', payload)

            elif action == 'delete_snapshot':
                success = config_logic.delete_snapshot(data.get('config_name'))
                if success:
                    payload = config_logic.scan_model()
                    palette = ui.palettes.itemById(palette_id)
                    palette.sendInfoToHTML('update_ui', payload)
                    
            elif action == 'load_snapshot':
                config_logic.apply_snapshot(data.get('config_name'))
                payload = config_logic.scan_model()
                palette = ui.palettes.itemById(palette_id)
                palette.sendInfoToHTML('update_ui', payload)

        except:
            if ui:
                ui.messageBox('HTML Event Failed:\n{}'.format(traceback.format_exc()))

# --- DOCUMENT SWITCH LISTENER ---
class MyDocActivatedHandler(adsk.core.DocumentEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            palette = ui.palettes.itemById(palette_id)
            if palette and palette.isVisible:
                payload = config_logic.scan_model()
                palette.sendInfoToHTML('update_ui', payload)
        except:
            pass 

class MyPaletteCloseHandler(adsk.core.UserInterfaceGeneralEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        pass

def run(context):
    global ui, app
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        cmdDefs = ui.commandDefinitions
        oldCmd = cmdDefs.itemById(command_id)
        if oldCmd: oldCmd.deleteMe()

        script_folder = os.path.dirname(os.path.realpath(__file__))
        resource_dir = os.path.join(script_folder, 'resources')
        
        cmdDef = cmdDefs.addButtonDefinition(
            command_id,
            'LiveConfig', 
            'Manage Parameters and Snapshots',
            resource_dir 
        )
        
        tool_clip_path = os.path.join(resource_dir, 'LiveConfigTooltipIcon.png')
        if os.path.exists(tool_clip_path):
            cmdDef.toolClipFilename = tool_clip_path
        
        onCommandCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        modify_panel = ui.allToolbarPanels.itemById('SolidModifyPanel')
        if modify_panel:
            control = modify_panel.controls.addCommand(cmdDef)
            control.isPromoted = False 
        
        onDocActivated = MyDocActivatedHandler()
        app.documentActivated.add(onDocActivated)
        handlers.append(onDocActivated)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        palette = ui.palettes.itemById(palette_id)
        if palette: palette.deleteMe()

        modify_panel = ui.allToolbarPanels.itemById('SolidModifyPanel')
        if modify_panel:
            cntrl = modify_panel.controls.itemById(command_id)
            if cntrl: cntrl.deleteMe()
            
        cmdDef = ui.commandDefinitions.itemById(command_id)
        if cmdDef: cmdDef.deleteMe()
    except:
        pass