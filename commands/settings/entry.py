#  Copyright 2023 by Ian Rist

import json
import adsk.core, adsk.fusion, adsk.cam, traceback
import os
from ...lib import fusion360utils as futil
from ... import config
from ... import shared_state
import time
import random
from typing import List
import math

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_Settings'
CMD_NAME = 'Fusion Essentials Settings'
CMD_Description = 'Change the settings and default behavior of Fusion Essentials'
IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = config.tools_panel_id
COMMAND_BESIDE_ID = ''

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

MODULE_PREFIX = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_'

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()

    if command_definition:
        command_definition.deleteMe()

def command_created(args):
    try:
        event_args = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = event_args.command
        inputs = cmd.commandInputs

        # Load all module settings
        all_module_settings = shared_state.get_all_module_settings()

        # Create a tab for each module
        for module_name, module_data in all_module_settings.items():
            tabCmdInput = inputs.addTabCommandInput(module_name, module_name[len(MODULE_PREFIX):])

            for setting_key, setting_metadata in module_data['settings'].items():
                if setting_metadata["type"] == "button" or setting_metadata["type"] == "checkbox":
                    tabCmdInput.children.addBoolValueInput(setting_key, setting_metadata["label"], setting_metadata["type"] == "checkbox", "", setting_metadata["default"])

                elif setting_metadata["type"] == "dropdown":
                    dropdown = tabCmdInput.children.addDropDownCommandInput(setting_key, setting_metadata["label"], adsk.core.DropDownStyles.TextListDropDownStyle)
                    for option in setting_metadata["options"]:
                        dropdown.listItems.add(option, option == setting_metadata["default"])

                # You can add support for more types as needed

        futil.add_handler(args.command.inputChanged, input_changed_handler, local_handlers=local_handlers)

    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def input_changed_handler(args: adsk.core.InputChangedEventArgs):
    try:
        changed_input = args.input

        # Assuming the id of the input matches the key in your settings
        setting_key = changed_input.id

        # Retrieve the module based on the parent (the tab) of the changed input
        module_name = changed_input.parentCommandInput.id

        # Load the existing settings for the module
        module_settings = shared_state.load_settings(module_name)

        # Depending on the type of input, you can get the value differently
        if isinstance(changed_input, adsk.core.DropDownCommandInput):
            selected_item = changed_input.selectedItem
            if selected_item:
                module_settings[setting_key]["default"] = selected_item.name

        elif isinstance(changed_input, adsk.core.BoolValueCommandInput):
            module_settings[setting_key]["default"] = changed_input.value

        # Save the modified settings back
        shared_state.save_settings(module_name, {"settings": module_settings})

    except:
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))