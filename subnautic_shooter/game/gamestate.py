# game/gamestate.py
import pygame
from os.path import join

from game.config import *
from game.map import MapSystem

from entities.player import Player
from entities.monster_spawner import MonsterSpawner
from entities.camera import Camera
from entities.player_respawn import RespawnSystem

from ui.hud import HUD
from ui.world_ui import WorldUI

class GameState:
    """Main gameplay state."""

    def __init__(
            self, 
            screen, 
            collision_sprites, 
            obstacle_group, 
            visible_sprites, 
            explosion_group
    ):
        self.screen = screen

        # sprite groups
        self.visible_sprites = visible_sprites
        self.collision_sprites = collision_sprites
        self.obstacle_group = obstacle_group
        self.explosion_group = explosion_group
        self.enemy_sprites = pygame.sprite.Group()
        self.portal_group = pygame.sprite.Group()
        self.check_portal_collisions_func = None

        # map
        self.map_system = MapSystem()
        self.map_surface = self.map_system.get_map_surface()
        self.collision_sprites = self.map_system.collision_sprites

        # assets
        self.explosion_frames = self.load_explosion_frames()
        self.sounds = self.load_audio()

        # camera
        self.camera = Camera(
            screen=self.screen,
            map_width=self.map_system.map_width,
            map_height=self.map_system.map_height
        )

        # player
        self.player = Player(
            pos=(self.map_system.map_width // 2, self.map_system.map_height // 2),
            group=self.visible_sprites,
            collision_sprites=self.collision_sprites,
            visible_sprites=self.visible_sprites,
            map_width=self.map_system.map_width,
            map_height=self.map_system.map_height,
            obstacle_group=self.obstacle_group,
            game_ref=self,
        )

        # monster spawner
        self.monster_spawner = MonsterSpawner(
            player=self.player,
            enemy_sprites=self.enemy_sprites,
            collision_sprites=self.collision_sprites,
            map_collision_sprites=self.map_system.collision_sprites,
            visible_sprites=self.visible_sprites
        )

        # respawn system
        self.respawn_system = RespawnSystem(self)

        # camera sprites        
        if hasattr(self.player, 'game_ref') and hasattr(self.player.game_ref, 'camera'):
            self.register_camera_sprites()

        # portal
        self.create_portals()

        # HUD
        self.hud = HUD(
            player=self.player,
            screen=self.screen,
            camera=self.camera,
        )
        # world UI
        self.world_ui = WorldUI(
            player=self.player,
            camera=self.camera,
            screen=self.screen
        )
        

    # ====== ASSET LOADING =====
    def load_explosion_frames(self):
        """Load explosion frames"""
        frames = []
        for i in range(6):
            try:
                img = pygame.image.load(join(EXPLOSION_PATH, f"{i}.png")).convert_alpha()
                frames.append(img)
            except Exception: # fallback: generate circles as explosion
                surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 100, 0), (16, 16), 16)
                frames.append(surf)
        return frames
        
    def load_audio(self):
        """Load sound effects to play for specific actions"""
        sounds = {}
        try:
            sounds["torpedo_launch"] = pygame.mixer.Sound(TORPEDO_LAUNCH_SOUND)
            sounds["torpedo_hit"] = pygame.mixer.Sound(TORPEDO_HIT_SOUND)
            sounds["sonar_ping"] = pygame.mixer.Sound(SONAR_PING)
            sounds["low_health"] = pygame.mixer.Sound(LOW_HEALTH_ALERT)
            sounds["respawn"] = pygame.mixer.Sound(IM_BACK)
            sounds["projectile_hit"] = sounds["torpedo_hit"]
            sounds['damage'] = pygame.mixer.Sound(DAMAGE_SOUND)
            sounds['teleport'] = pygame.mixer.Sound(TELEPORT_SOUND)
        except Exception as e:
            print(f"Failed to load audio: {e}")
        return sounds

    # ===== SETUP HELPERS =====
    def register_camera_sprites(self):
        """Register all drawable sprites to the camera"""
        self.camera.add(self.player)
        for sprite in self.visible_sprites:
            self.camera.add(sprite)
    
    def register_new_sprite(self, sprite):
        self.camera.add(sprite)
        if sprite not in self.visible_sprites:
            self.visible_sprites.add(sprite)

    def create_portals(self):
        try:
            from entities.portal import create_portal_network, check_portal_collisions

            self.portal_group = create_portal_network(
                self.visible_sprites,
                self.camera,
                self
            )
            self.check_portal_collisions_func = check_portal_collisions
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.portal_group = pygame.sprite.Group()
            self.check_portal_collisions_func = None 

    # ===== INTERNAL LOGIC =====
    def update_monster_player_target(self):
        target = None if self.player.is_invincible else self.player
        for monster in self.enemy_sprites:
            monster.player = target

    # ===== UPDATE & DRAW =====
    def update(self, dt):
        self.visible_sprites.update(dt)
        self.enemy_sprites.update(dt)
        self.explosion_group.update(dt)
        self.monster_spawner.update(dt)
        self.respawn_system.update(dt)
        self.portal_group.update(dt)

        if self.portal_group:
            from entities.portal import check_portal_collisions
            check_portal_collisions(
                self.portal_group,
                self.player,
                pygame.time.get_ticks()
            )

        self.camera.centered_player_cam(self.player)
        self.update_monster_player_target()

    def draw(self, screen, dt=1/60):
        # map
        screen.blit(self.map_surface, -self.camera.offset)
        # camera world sprites
        self.camera.custom_draw(self.player)
        # explosions
        for explosion in self.explosion_group:
            pos = pygame.math.Vector2(explosion.rect.topleft) - self.camera.offset
            screen.blit(explosion.image, pos)
        # world UI
        self.world_ui.draw(self.enemy_sprites)
        # torpedo trajectory
        if not self.player.is_dead:
            self.player.draw_trajectory(screen, self.camera.offset, dt)
        # HUD
        self.hud.draw(self.enemy_sprites, self.camera.offset)

                