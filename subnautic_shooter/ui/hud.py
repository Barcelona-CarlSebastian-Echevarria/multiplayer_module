# entities/ui/hud.py
import pygame
from game.config import *


class HUD:
    """Heads-up display for player stats, abilities, portals, and overlays."""

    def __init__(self, player, screen, camera=None):
        self.player = player
        self.screen = screen
        self.camera = camera

        # fonts
        self.font = pygame.font.Font(None, 28)
        self.large_font = pygame.font.Font(None, 72)
        self.medium_font = pygame.font.Font(None, 36)

        self.portal_title_font = pygame.font.SysFont("arial", 16, bold=True)
        self.portal_hint_font = pygame.font.SysFont("arial", 13)

        self.icon_font = pygame.font.SysFont("arial", 14, bold=True)

        # layout
        self.ui_x = 20
        self.ui_y = 20
        self.line_height = 40

        self.cursor_y = self.ui_y

        # bar config
        self.bar_width = 300
        self.bar_height = 20
        self.bar_border = 2

        # colors
        self.text_color = (255, 255, 255)
        self.border_color = (200, 200, 200)

        self.health_bg = (100, 100, 100)
        self.health_fg = (220, 50, 50)

        self.xp_bg = (80, 80, 80)
        self.xp_fg = (50, 180, 255)

        # fog
        self.fog_surface = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        # ability icon layout
        self.icon_size = 48
        self.icon_padding = 12

        self.icon_y = SCREEN_HEIGHT - self.icon_size - 20
        self.icon_start_x = SCREEN_WIDTH - (self.icon_size * 3) - (self.icon_padding * 2) - 20

        # load icons
        self.torpedo_icon = self.load_icon(TORPEDO_ICON_PATH)
        self.sonar_icon = self.load_icon(SONAR_ICON_PATH)
        self.portal_icon = self.load_icon(PORTAL_ICON_PATH)

    # ===== HELPERS =====
    def next_y(self):
        """Advance vertical cursor for stacked HUD elements."""
        y = self.cursor_y
        self.cursor_y += self.line_height
        return y

    def draw_bar(self, text, ratio, y, fg_color, bg_color):
        """Generic labeled progress bar."""
        text_surf = self.font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(topleft=(self.ui_x, y))
        self.screen.blit(text_surf, text_rect)

        bar_x = text_rect.right + 15
        bar_y = y + (text_rect.height - self.bar_height) // 2
        bar_rect = pygame.Rect(bar_x, bar_y, self.bar_width, self.bar_height)

        pygame.draw.rect(self.screen, bg_color, bar_rect)

        if ratio > 0:
            fill_rect = bar_rect.copy()
            fill_rect.width = int(self.bar_width * ratio)
            pygame.draw.rect(self.screen, fg_color, fill_rect)

        pygame.draw.rect(self.screen, self.border_color, bar_rect, self.bar_border)

    def load_icon(self, path):
        try:
            icon = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(icon, (self.icon_size, self.icon_size))
        except Exception:
            surf = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            pygame.draw.rect(surf, (120, 120, 120), surf.get_rect(), 2)
            return surf
        
    def draw_icon_with_cooldown(self, icon, x, y, cooldown_ratio, disabled=False, label=None):
        """Draw icon with cooldown overlay and optional disabled state."""
        self.screen.blit(icon, (x, y))

        if disabled:
            overlay = pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (x, y))

        if cooldown_ratio > 0:
            h = int(self.icon_size * cooldown_ratio)
            cd_rect = pygame.Rect(x, y + (self.icon_size - h), self.icon_size, h)
            overlay = pygame.Surface(cd_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, cd_rect.topleft)

        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (x, y, self.icon_size, self.icon_size),
            2
        )

        if label:
            text = self.icon_font.render(label, True, (255, 255, 255))
            self.screen.blit(text, (x + 4, y + self.icon_size + 2))

    # ===== PLAYER BARS =====
    def draw_health(self):
        ratio = self.player.health / self.player.max_health
        y = self.next_y()
        self.draw_bar(
            f"Health: {self.player.health}/{self.player.max_health}",
            ratio,
            y,
            self.health_fg,
            self.health_bg
        )

    def draw_xp(self):
        y = self.next_y()

        if self.player.level >= self.player.max_level:
            text = f"Level {self.player.level}: MAX LEVEL"
            ratio = 1.0
        else:
            xp_needed = self.player.xp_to_next[self.player.level]
            ratio = min(1.0, self.player.xp / xp_needed)
            text = f"Level {self.player.level}: {self.player.xp}/{xp_needed} XP"

        self.draw_bar(text, ratio, y, self.xp_fg, self.xp_bg)

    def draw_power(self):
        y = self.next_y()
        ratio = self.player.power / self.player.max_power

        if ratio > 0.7:
            color = (50, 200, 50)
        elif ratio > 0.3:
            color = (200, 200, 50)
        else:
            color = (220, 100, 50)

        self.draw_bar(
            f"Power: {int(self.player.power)}/{self.player.max_power}",
            ratio,
            y,
            color,
            self.xp_bg
        )

    # ===== PORTAL INFO =====
    def draw_portal_info(self):
        """Draw active portal info when player is near a portal."""
        portal = self.player.current_portal
        if not portal:
            return

        y = self.next_y()

        index = portal.node.portal_index + 1
        next_i = portal.node.next.portal_index + 1
        prev_i = portal.node.prev.portal_index + 1

        title = self.portal_title_font.render(
            f"Portal {index}", True, (0, 255, 0)
        )
        hint = self.portal_hint_font.render(
            f"E → Portal {next_i}    Q ← Portal {prev_i}",
            True, (180, 255, 180)
        )

        self.screen.blit(title, (self.ui_x, y))
        self.screen.blit(hint, (self.ui_x, y + 18))

        self.cursor_y += 10  # extra spacing

    # ===== ABILITY ICONS =====    
    def draw_torpedo_icon(self, x, y):
        current = pygame.time.get_ticks()
        elapsed = (current - self.player.last_torpedo_time) / 1000
        cd = self.player.torpedo_cooldown

        cooldown_ratio = max(0, 1 - (elapsed / cd)) if elapsed < cd else 0
        disabled = self.player.power < self.player.torpedo_cost

        self.draw_icon_with_cooldown(
            self.torpedo_icon,
            x, y,
            cooldown_ratio,
            disabled,
            "SPACE"
        )
    
    def draw_sonar_icon(self, x, y):
        current = pygame.time.get_ticks()

        if self.player.level < self.player.sonar_level_required:
            self.draw_icon_with_cooldown(
                self.sonar_icon,
                x, y,
                0,
                True,
                "LOCK"
            )
            return

        elapsed = (current - self.player.last_sonar_time) / 1000
        cd = self.player.sonar_cooldown
        cooldown_ratio = max(0, 1 - (elapsed / cd)) if elapsed < cd else 0

        disabled = self.player.power < self.player.sonar_cost

        if self.player.sonar_active:
            pygame.draw.rect(
                self.screen,
                (50, 200, 255),
                (x - 2, y - 2, self.icon_size + 4, self.icon_size + 4),
                3
            )

        self.draw_icon_with_cooldown(
            self.sonar_icon,
            x, y,
            cooldown_ratio,
            disabled,
            "F"
        )

    def draw_portal_icon(self, x, y):
        current = pygame.time.get_ticks()
        elapsed = (current - self.player.last_portal_time) / 1000
        cooldown_ratio = max(0, 1 - (elapsed / PORTAL_COOLDOWN)) if elapsed < PORTAL_COOLDOWN else 0

        disabled = self.player.current_portal is None

        self.draw_icon_with_cooldown(
            self.portal_icon,
            x, y,
            cooldown_ratio,
            disabled,
            "E / Q"
        )

    # ===== POST-DEATH/RESPAWN SCREEN =====
    def draw_respawn_overlay(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        died = self.large_font.render("YOU DIED", True, (255, 50, 50))
        self.screen.blit(
            died,
            died.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        )

        elapsed = (pygame.time.get_ticks() - self.player.respawn_timer) / 1000
        remaining = max(0, RESPAWN_DELAY - elapsed)

        timer = self.medium_font.render(
            f"Respawning in {remaining:.1f}s...", True, (255, 255, 255)
        )
        self.screen.blit(
            timer,
            timer.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        )

    def draw_invincibility(self):
        if not self.player.is_invincible or self.player.is_dead:
            return

        elapsed = (pygame.time.get_ticks() - self.player.invincibility_timer) / 1000
        remaining = max(0, RESPAWN_PROTECTION_TIME - elapsed)

        text = self.font.render(
            f"INVULNERABLE: {remaining:.1f}s", True, (255, 255, 0)
        )
        rect = text.get_rect(center=(self.screen.get_width() // 2, 30))
        self.screen.blit(text, rect)

    # ===== DRAW =====
    def draw(self, monsters=None, camera_offset=None):
        """Draw all HUD elements."""
        self.cursor_y = self.ui_y

        if self.player.is_dead:
            self.draw_respawn_overlay()
            return
        
        x = self.icon_start_x
        y = self.icon_y

        self.draw_health()
        self.draw_xp()
        self.draw_power()
        self.draw_portal_info()
        self.draw_invincibility()

        self.draw_torpedo_icon(x, y)
        self.draw_sonar_icon(x + self.icon_size + self.icon_padding, y)
        self.draw_portal_icon(x + (self.icon_size + self.icon_padding) * 2, y)
