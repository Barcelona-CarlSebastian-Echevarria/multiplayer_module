# create_wait_popup.py - Popup for waiting for host to accept

import pygame_gui
import pygame

class WaitingPopup:
    def __init__(self, ui_manager, screen_size):
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(
                (screen_size[0] // 2 - 200, screen_size[1] // 2 - 80),
                (400, 160)
            ),
            manager=ui_manager,
            window_display_title="Please wait",
            object_id="#waiting_popup",
            visible=False
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 40, 360, 40),
            text="Waiting for host to accept...",
            manager=ui_manager,
            container=self.window
        )

    def show(self):
        self.window.show()

    def hide(self):
        self.window.hide()
