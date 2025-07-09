import pygame
import pygame_gui
import os


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
                    return self.dialog_type, self.refine_pathname(event.text)
                    
            elif event.user_type == pygame_gui.UI_WINDOW_CLOSE:
                if event.ui_element == self.active_dialog:
                    self.active_dialog = None
        return None, None
    
    def refine_pathname(self, path):
        if self.dialog_type != "save":
            return path
        if path.endswith(".cogogame"):
            return path
        
        return path + ".cogogame"
    
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
                    initial_file_path=os.getcwd(),
                    allow_existing_files_only=True,
                    allowed_suffixes=[".cogogame"]
                )
            self.dialog_type = "open"  
            
        elif load_or_save == "save":
            self.active_dialog = pygame_gui.windows.UIFileDialog(
                rect=self.rect,
                manager=self.manager,
                window_title="Save File...",
                initial_file_path=os.getcwd(),
                allow_existing_files_only=False,
                allowed_suffixes=[".cogogame"]
            )
            self.dialog_type = "save" 
