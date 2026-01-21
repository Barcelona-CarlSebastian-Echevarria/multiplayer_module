# ui/world_ui.py
import pygame
from game.config import *


class WorldUI:
    """Handles world-space UI and visual effects"""

    def __init__(self, player, camera, screen):
        self.player = player
        self.camera = camera
        self.screen = screen

        # fog setup
        self.fog_surface = pygame.Surface(
            screen.get_size(),
            flags=pygame.SRCALPHA
        )

    # ===== SONAR WAVES =====
    def draw_sonar_waves(self):
        if not self.player or not self.player.sonar_active:
            return

        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.player.sonar_start_time) / 1000.0

        if elapsed >= self.player.sonar_duration:
            return

        player_pos = pygame.math.Vector2(self.player.rect.center) - self.camera.offset
        screen_width, screen_height = self.screen.get_size()

        pulse_alpha = int(100 * (1 - (elapsed / self.player.sonar_duration)))
        pulse_alpha = max(0, min(100, pulse_alpha))

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((255, 255, 100, pulse_alpha))

        for i in range(3):
            wave_time = elapsed - (i * 0.5)
            if wave_time < 0:
                continue

            radius = int(wave_time * 600)
            if radius > max(screen_width, screen_height):
                continue

            wave_alpha = int(150 * (1 - (wave_time / 1.5)))
            wave_alpha = max(0, min(150, wave_alpha))

            if wave_alpha > 0:
                pygame.draw.circle(
                    overlay,
                    (255, 255, 200, wave_alpha),
                    (int(player_pos.x), int(player_pos.y)),
                    radius,
                    5
                )

        self.screen.blit(overlay, (0, 0))


    # ===== FOG EFFECTS =====
    def draw_fog(self):
        if not self.player:
            return
        
        if self.player.sonar_active:
            return

        self.fog_surface.fill((0, 0, 0, FOG_ALPHA))
        offset = self.camera.offset if self.camera else pygame.Vector2()
        pos = self.player.rect.center - offset

        for r in range(FOG_RADIUS, VISIBILITY_RADIUS, -6):
            alpha = int(
                FOG_ALPHA * (r - VISIBILITY_RADIUS)
                / (FOG_RADIUS - VISIBILITY_RADIUS)
            )
            pygame.draw.circle(self.fog_surface, (0, 0, 0, alpha), pos, r)

        pygame.draw.circle(self.fog_surface, (0, 0, 0, 0), pos, VISIBILITY_RADIUS)
        self.screen.blit(self.fog_surface, (0, 0))

    # ===== MONSTER HEALTH BARS =====
    def draw_monster_health_bars(self, monsters):
        for monster in monsters:
            if monster.health >= monster.max_health:
                continue

            if getattr(monster, "alpha", 255) <= 40:
                continue

            screen_x = monster.rect.centerx - self.camera.offset.x
            screen_y = monster.rect.top - self.camera.offset.y - 10

            bar_width = 40
            bar_height = 4
            health_ratio = max(0, monster.health / monster.max_health)

            pygame.draw.rect(
                self.screen,
                (150, 0, 0),
                (screen_x - bar_width // 2, screen_y, bar_width, bar_height)
            )

            if health_ratio > 0:
                fill_width = int(bar_width * health_ratio)

                if health_ratio > 0.5:
                    color = (0, 200, 0)
                elif health_ratio > 0.25:
                    color = (255, 165, 0)
                else:
                    color = (255, 0, 0)

                pygame.draw.rect(
                    self.screen,
                    color,
                    (screen_x - bar_width // 2, screen_y, fill_width, bar_height)
                )

    def draw(self, monsters):
        self.draw_sonar_waves()
        self.draw_monster_health_bars(monsters)
        self.draw_fog()