import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UILabel, UITextEntryLine, UIButton


class StartProfilePopup:
    """
    CREATE PLAYER PROFILE POPUP (UI ONLY)

    Responsibilities:
    - Ask for player name
    - Validate basic input (non-empty)
    - Notify parent via callbacks

    Does NOT:
    - Write to database
    - Know game modes
    - Know server/client logic
    """

    def __init__(self, ui_manager, screen_size, on_confirm=None, on_cancel=None):
        self.ui_manager = ui_manager
        self.screen_width, self.screen_height = screen_size

        # Callbacks
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        # UI elements
        self.window = None
        self.name_input = None
        self.confirm_button = None
        self.cancel_button = None
        self.error_label = None

    # ==================================================
    # ================= PUBLIC API =====================
    # ==================================================

    def show(self):
        if self.window is not None:
            # ADD THIS: If window exists but is hidden/dead, recreate it
            if not self.window.alive():
                self.window = None
            else:
                return  # Prevent duplicate popups

        self.window = UIWindow(
            rect=pygame.Rect(
                (self.screen_width // 2 - 200, self.screen_height // 2 - 130),
                (400, 260)
            ),
            manager=self.ui_manager,
            window_display_title="Create Player Profile",
        )

        UILabel(
            relative_rect=pygame.Rect(20, 20, 360, 30),
            text="Enter Player Name",
            manager=self.ui_manager,
            container=self.window
        )

        self.name_input = UITextEntryLine(
            relative_rect=pygame.Rect(20, 55, 360, 35),
            manager=self.ui_manager,
            container=self.window
        )

        self.error_label = UILabel(
            relative_rect=pygame.Rect(20, 95, 360, 30),
            text="",
            manager=self.ui_manager,
            container=self.window
        )

        self.confirm_button = UIButton(
            relative_rect=pygame.Rect(40, 150, 130, 40),
            text="CONFIRM",
            manager=self.ui_manager,
            container=self.window
        )

        self.cancel_button = UIButton(
            relative_rect=pygame.Rect(230, 150, 130, 40),
            text="CANCEL",
            manager=self.ui_manager,
            container=self.window
        )

    def close(self):
        if self.window:
            self.window.kill()
            self.window = None
    
    def reset(self):
        """Reset the popup so it can be shown again"""
        self.window = None

    # ==================================================
    # ================= EVENT HANDLING =================
    # ==================================================

    def process_event(self, event):
        if event.type != pygame_gui.UI_BUTTON_PRESSED:
            return

        if event.ui_element == self.confirm_button:
            name = self.name_input.get_text().strip()

            if not name:
                self.error_label.set_text("Name cannot be empty.")
                return

            if self.on_confirm:
                self.on_confirm(name)

            self.close()

        elif event.ui_element == self.cancel_button:
            if self.on_cancel:
                self.on_cancel()

            self.close()
