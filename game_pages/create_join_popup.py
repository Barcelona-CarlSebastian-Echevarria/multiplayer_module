# This is create_join_popup.py - Popup for joining a multiplayer lobby

import pygame_gui
import pygame

class JoinLobbyPopup:
    def __init__(self, ui_manager, screen_size, on_confirm, on_cancel):
        self.ui_manager = ui_manager
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(
                (screen_size[0] // 2 - 200, screen_size[1] // 2 - 120),
                (400, 240)
            ),
            manager=ui_manager,
            window_display_title="Join Lobby",
            object_id="#join_lobby_popup",
            visible=False
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 20, 360, 30),
            text="Enter lobby passcode:",
            manager=ui_manager,
            container=self.window
        )

        self.passcode_input = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(20, 60, 360, 35),
            manager=ui_manager,
            container=self.window
        )
        self.passcode_input.set_text_hidden(True)

        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(40, 140, 140, 40),
            text="JOIN",
            manager=ui_manager,
            container=self.window
        )

        self.cancel_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(220, 140, 140, 40),
            text="CANCEL",
            manager=ui_manager,
            container=self.window
        )

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.confirm_button:
                self.on_confirm(self.passcode_input.get_text())
                # self.hide()

            elif event.ui_element == self.cancel_button:
                self.on_cancel()
                # self.hide()
