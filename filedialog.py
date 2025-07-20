from dotenv import set_key, load_dotenv
from pathlib import Path
import os

import pygame
import pygame_gui

from utils import get_readable_filepath


FILEPATH_VAR_NAME = "sugo_last_picked_directory"
def get_dir():
    load_dotenv(override=True)
    return os.getenv(FILEPATH_VAR_NAME) or os.getcwd()


def set_dir(new_dir):
    set_key(".env", FILEPATH_VAR_NAME, str(new_dir))



class FileDailog:
    def __init__(self, rect, manager):
        self.rect = rect
        self.manager = manager
        self.active_dialog = None
        self.dialog_type = None

    def handle_event(self, event):
        """Handle UI events"""
        if event.type == pygame.USEREVENT:            
            if event.user_type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                print(f"Picked path: {event.text}")
                if event.ui_element == self.active_dialog:
                    self.active_dialog = None
                    set_dir(Path(event.text).parent)
                    return self.dialog_type, self.refine_pathname(event.text)
                    
            elif event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.active_dialog:
                    self.active_dialog = None
        return None, None
    
    def refine_pathname(self, path):
        if self.dialog_type != "save":
            return path
        if path.endswith(".sugo"):
            return path
        
        return path + ".sugo"
    
    def is_active(self):
        return self.active_dialog is not None
    
    def open_file_dialog(self, load_or_save):
        if self.is_active():
            print("Dialog is already opened. Please close or ok it before opening next dialog")
            print(self.active_dialog)
            return

        if load_or_save == "open":
            self.active_dialog = pygame_gui.windows.UIFileDialog(
                    rect=self.rect,
                    manager=self.manager,
                    window_title="Load File...",
                    initial_file_path=get_dir(),
                    allow_existing_files_only=True,
                    allowed_suffixes=[".sugo"]
                )
            self.dialog_type = "open"  
            
        elif load_or_save == "save":
            self.active_dialog = pygame_gui.windows.UIFileDialog(
                rect=self.rect,
                manager=self.manager,
                window_title="Save File...",
                initial_file_path=str(Path(get_dir()) / get_readable_filepath()),
                allow_existing_files_only=False,
                allowed_suffixes=[".sugo"]
            )
            self.dialog_type = "save" 
