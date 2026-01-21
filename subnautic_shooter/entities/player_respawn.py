# entities/player_respawn.py
import pygame
from random import shuffle
from game.config import *

class RespawnSystem:
    """Handles player death, respawn timing, and invincibility"""
    def __init__(self, game_state):
        self.game_state = game_state
        self.player = game_state.player
        
        # respawn points
        self.respawn_points = RESPAWN_POINTS[:]  
        shuffle(self.respawn_points)  # shuffle for fun
        self.current_respawn_index = 0
        
        # respawn state
        self.is_respawning = False
        self.respawn_timer = 0
        
        # invincibility
        self.is_invincible = False
        self.invincibility_timer = 0
        self.flash_timer = 0
        self.visible = True  # for flashing effect
            
    # ===== RESPAWN LOGIC =====
    def get_safe_respawn_point(self):
        monsters = self.game_state.enemy_sprites
        collision_sprites = self.game_state.collision_sprites

        for _ in range(len(self.respawn_points)):
            point = pygame.math.Vector2(self.respawn_points[self.current_respawn_index])
            safe = True

            for monster in monsters:
                if pygame.math.Vector2(monster.rect.center).distance_to(point) < RESPAWN_SAFE_RADIUS:
                    safe = False
                    break

            if safe:
                temp_rect = self.player.rect.copy()
                temp_rect.center = point
                for sprite in collision_sprites:
                    if temp_rect.colliderect(sprite.rect):
                        safe = False
                        break

            self.current_respawn_index = (self.current_respawn_index + 1) % len(self.respawn_points)

            if safe:
                return point

        return pygame.math.Vector2(self.respawn_points[0])

    def start_respawn(self):
        """Start the respawn process"""
        if not self.is_respawning and self.player.health <= 0:
            self.is_respawning = True
            self.respawn_timer = pygame.time.get_ticks()
            print(f"Respawning in {RESPAWN_DELAY} seconds...")
    
    def execute_respawn(self, current_time):
        """Respawns the player"""
        spawn_pos = self.get_safe_respawn_point()
        self.player.respawn(spawn_pos)

        self.is_invincible = True
        self.invincibility_timer = current_time
        self.flash_timer = current_time
        self.visible = True

        # remove active torpedoes
        for sprite in self.game_state.visible_sprites:
            if getattr(sprite, "is_torpedo", False):
                sprite.kill()
            
        self.is_respawning = False

        self.game_state.camera.centered_player_cam(self.player)
        print(f"Player respawned at {spawn_pos}")            

    # ===== INVINCIBILITY =====
    def update_invincibility(self, current_time):
        """Update invincibility state and flashing effect"""
        elapsed = (current_time - self.invincibility_timer) / 1000

        if elapsed >= RESPAWN_PROTECTION_TIME:
            self.is_invincible = False
            self.player.image.set_alpha(255)
            return

        if current_time - self.flash_timer >= RESPAWN_FLASH_INTERVAL:
            self.visible = not self.visible
            self.flash_timer = current_time
            self.player.image.set_alpha(255 if self.visible else 100)
    
    # ===== UPDATE & DEBUG =====

    def update(self, dt):
            current_time = pygame.time.get_ticks()

            if self.is_respawning:
                elapsed = (current_time - self.respawn_timer) / 1000
                if elapsed >= RESPAWN_DELAY:
                    self.execute_respawn(current_time)

            if self.is_invincible:
                elapsed = (current_time - self.respawn_timer) / 1000
                if elapsed >= RESPAWN_PROTECTION_TIME:
                    self.is_invincible = False
                    self.player.image.set_alpha(255)
                else:
                    if current_time - self.flash_timer >= RESPAWN_FLASH_INTERVAL:
                        self.visible = not self.visible
                        self.flash_timer = current_time
                        self.player.image.set_alpha(255 if self.visible else 100)

    def draw_debug(self, screen):
        if not self.waiting_for_respawn:
            return

        elapsed = (pygame.time.get_ticks() - self.respawn_timer) / 1000
        remaining = max(0, RESPAWN_DELAY - elapsed)

        text = f"Respawning in: {remaining:.1f}s"
        surf = self.debug_font.render(text, True, (255, 255, 255))
        screen.blit(surf, (20, 100))