import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UILabel, UITextEntryLine, UIButton


class CreateLobbyPopup:
    """
    CREATE LOBBY POPUP (UI ONLY)

    Responsibilities:
    - Render modal popup
    - Collect lobby name and passcode
    - Notify parent via callbacks
    """

    def __init__(self, ui_manager, screen_size, on_confirm=None, on_cancel=None):
        self.ui_manager = ui_manager
        self.screen_width, self.screen_height = screen_size

        # Callbacks
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        # UI elements
        self.window = None
        self.lobby_name_input = None
        self.passcode_input = None
        self.confirm_button = None
        self.cancel_button = None

    # ==================================================
    # ================= PUBLIC API =====================
    # ==================================================

    def show(self):
        if self.window is not None:
            return  # Prevent duplicate popups

        self.window = UIWindow(
            rect=pygame.Rect(
                (self.screen_width // 2 - 200, self.screen_height // 2 - 150),
                (400, 300)
            ),
            manager=self.ui_manager,
            window_display_title="Create Lobby",
        )

        # Lobby name
        UILabel(
            relative_rect=pygame.Rect(20, 20, 360, 30),
            text="Lobby Name",
            manager=self.ui_manager,
            container=self.window
        )

        self.lobby_name_input = UITextEntryLine(
            relative_rect=pygame.Rect(20, 50, 360, 35),
            manager=self.ui_manager,
            container=self.window
        )

        # Passcode
        UILabel(
            relative_rect=pygame.Rect(20, 100, 360, 30),
            text="Passcode",
            manager=self.ui_manager,
            container=self.window
        )

        self.passcode_input = UITextEntryLine(
            relative_rect=pygame.Rect(20, 130, 360, 35),
            manager=self.ui_manager,
            container=self.window
        )
        self.passcode_input.set_text_hidden(False)

        # Buttons
        self.confirm_button = UIButton(
            relative_rect=pygame.Rect(40, 200, 130, 40),
            text="CONFIRM",
            manager=self.ui_manager,
            container=self.window
        )

        self.cancel_button = UIButton(
            relative_rect=pygame.Rect(230, 200, 130, 40),
            text="CANCEL",
            manager=self.ui_manager,
            container=self.window
        )

    def close(self):
        if self.window:
            self.window.kill()
            self.window = None

    # ==================================================
    # ================= EVENT HANDLING =================
    # ==================================================

    def process_event(self, event):
        if event.type != pygame_gui.UI_BUTTON_PRESSED:
            return

        if event.ui_element == self.confirm_button:
            lobby_name = self.lobby_name_input.get_text()
            passcode = self.passcode_input.get_text()

            if self.on_confirm:
                self.on_confirm(lobby_name, passcode)

            self.close()

        elif event.ui_element == self.cancel_button:
            if self.on_cancel:
                self.on_cancel()

            self.close()
