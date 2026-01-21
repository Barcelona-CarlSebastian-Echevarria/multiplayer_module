import pygame
import pygame_gui


class ProfileWidget:
    """
    Top-corner profile display widget.

    Responsibilities:
    - Display current player name or 'no account'
    - Visual hover feedback
    - Open stats popup on click
    """

    def __init__(self, ui_manager, screen_width):
        self.ui_manager = ui_manager

        # Position & size (top-right)
        self.rect = pygame.Rect(screen_width - 320, 20, 300, 90)

        # State
        self.profile = None
        self.hovered = False

        # Colors (FLAVOR ✨)
        self.bg_idle = (20, 30, 50)
        self.bg_hover = (40, 70, 120)
        self.border = (120, 180, 255)
        self.text_main = (220, 230, 255)
        self.text_sub = (170, 190, 220)

        # Fonts (pygame default-safe)
        self.font_main = pygame.font.SysFont("arial", 20, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 14)

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def set_profile(self, profile):
        """Update displayed profile"""
        self.profile = profile

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos, on_no_profile, on_show_stats):
        if not self.rect.collidepoint(mouse_pos):
            return False

        if self.profile:
            on_show_stats()
        else:
            on_no_profile()

        return True

    def draw(self, surface):
        # Background
        bg_color = self.bg_hover if self.hovered else self.bg_idle
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=12)
        pygame.draw.rect(surface, self.border, self.rect, 2, border_radius=12)

        # Content
        if self.profile:
            name_text = f"{self.profile[1]}"
            hint_text = "View player stats"
        else:
            name_text = "No account logged in"
            hint_text = "Click to create profile"

        name_surf = self.font_main.render(name_text, True, self.text_main)
        hint_surf = self.font_sub.render(hint_text, True, self.text_sub)

        surface.blit(name_surf, (self.rect.x + 14, self.rect.y + 18))
        surface.blit(hint_surf, (self.rect.x + 14, self.rect.y + 50))

    # -------------------------------------------------
    # Stats Popup
    # -------------------------------------------------

    def show_stats_popup(self):
        if not self.profile:
            return

        local_id, name, games, wins, losses, best_survival = self.profile

        window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(420, 200, 440, 360),
            manager=self.ui_manager,
            window_display_title="Player Statistics"
        )

        labels = [
            f"Name: {name}",
            f"ID: {local_id}",
            f"Games Played: {games}",
            f"Wins: {wins}",
            f"Losses: {losses}",
            "",
            "BEST SURVIVAL RECORD",
            f"{best_survival} seconds"
        ]

        y = 20
        for text in labels:
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(20, y, 400, 30),
                text=text,
                manager=self.ui_manager,
                container=window
            )
            y += 35
