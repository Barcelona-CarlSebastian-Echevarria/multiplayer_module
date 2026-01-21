# entities/player.py
import pygame
from os.path import join
from game.config import *
from entities.torpedo import Torpedo
import os

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

PLAYER_ASSETS = join(
    PROJECT_ROOT,
    "subnautic_shooter",
    "assets",
    "images",
    "player"
)

class Player(pygame.sprite.Sprite):
    def __init__(self, 
            pos, 
            group, 
            collision_sprites, 
            visible_sprites, 
            map_width, 
            map_height, 
            obstacle_group=None, 
            game_ref=None
    ):
        super().__init__(group)

        # references
        self.game_ref = game_ref
        self.visible_sprites = visible_sprites
        self.collision_sprites = collision_sprites
        self.obstacle_group = obstacle_group

        self.explosion_frames = game_ref.explosion_frames if game_ref else []
        self.explosion_group = game_ref.explosion_group if game_ref else None

        # movement & direction
        self.direction = pygame.math.Vector2()
        self.last_horizontal = 'right'

        self.speed = PLAYER_SPEED
        self.normal_speed = PLAYER_SPEED
        self.boost_speed = BOOST_SPEED

        # health & damage
        self.max_health = PLAYER_HEALTH
        self.health = self.max_health

        self.hp_regen_rate = 0.0
        self.last_damage_time = 0
        self.last_hit_time = 0
        self.hit_cooldown = TAKE_DAMAGE_CD
        self.is_hit = False
        self.hit_timer = 0.0
        self.hit_flash_duration = 0.2 # seconds

        self.base_damage = PLAYER_BASE_DAMAGE
        self.damage = self.base_damage

        # death & invincibility
        self.is_dead = False
        self.is_invincible = False
        self.invincibility_timer = 0
        self.last_flash_time = 0
        self.flash_visible = True
        self.respawn_timer = 0

        # power core
        self.max_power = PLAYER_MAX_POWER
        self.power = self.max_power
        self.power_regen_rate = POWER_REGEN

        self.boost_cost = BOOST_COST
        self.torpedo_cost = TORPEDO_COST

        # XP & level system
        self.level = 1
        self.max_level = PLAYER_MAX_LEVEL
        self.xp = 0

        self.xp_to_next = [0]
        for lvl in range(1, self.max_level + 1):
            self.xp_to_next.append(50 + (lvl - 1) * 25)
        
        # torpedoes
        self.torpedo_cooldown = TORPEDO_COOLDOWN
        self.last_torpedo_time = 0

        # sonar activation
        self.sonar_level_required = SONAR_LEVEL_REQUIRED
        self.sonar_active = False
        self.sonar_duration = SONAR_DURATION
        self.sonar_start_time = 0
        self.sonar_cooldown = SONAR_COOLDOWN
        self.last_sonar_time = -9999
        self.sonar_cost = SONAR_COST
        self.sonar_range = SONAR_RANGE

        # portal interaction
        self.current_portal = None
        self.portal_interaction_radius = 100
        self.last_portal_time = -9999
        self.portal_cooldown = PORTAL_COOLDOWN

        # world bounds
        self.map_width = map_width
        self.map_height = map_height

        # animation & rendering
        self.load_animation()
        self.current_animation = 'right'
        self.animation_frame = 0
        self.animation_speed = 0.15
        self.animation_timer = 0

        self.image = self.animations[self.current_animation][0]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.copy()

        # crosshair & aiming
        self.crosshair_length = 50 # pixels
        self.crosshair_pos = pygame.math.Vector2(self.rect.center)
        self.aim_direction = pygame.math.Vector2(1, 0)

        # load audio
        # in Player.__init__
        self.sounds = game_ref.sounds if game_ref else {}

        sound_folder = os.path.join(PROJECT_ROOT, "subnautic_shooter", "assets", "audio", "sound_effects")

        self.sounds = {
            'torpedo_launch': pygame.mixer.Sound(os.path.join(sound_folder, "projectile_launch.mp3")),
            'damage': pygame.mixer.Sound(os.path.join(sound_folder, "damage.mp3")),
            'low_health': pygame.mixer.Sound(os.path.join(sound_folder, "low_health.mp3")),
            'sonar_ping': pygame.mixer.Sound(os.path.join(sound_folder, "sonar_ping.mp3")),
            'respawn': pygame.mixer.Sound(os.path.join(sound_folder, "respawn.mp3")),
            'teleport': pygame.mixer.Sound(os.path.join(sound_folder, "teleport.mp3")),
            'im_back': pygame.mixer.Sound(os.path.join(sound_folder, "im_back.mp3"))
        }

        self.update_hp_regen_rate()

    # ===== INPUT & MOVEMENT =====
    def input(self, dt):
        """Handles user input to perform actions/motion"""
        if self.is_dead: # no input while dead
            return
        
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()

        # movement (WASD)
        x_input = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        y_input = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        self.direction.x = x_input
        self.direction.y = y_input

        if x_input != 0:
            self.last_horizontal = 'right' if x_input > 0 else 'left'

        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        # boost (Lshift)
        if keys[pygame.K_LSHIFT] and self.power > 0:
            self.speed = self.boost_speed
            self.power -= self.boost_cost * dt
            self.power = max(0, self.power)
        else:
            self.speed = self.normal_speed

        # torpedo launching (left click or space)
        can_fire = self.power >= self.torpedo_cost
        current_time = pygame.time.get_ticks()
        if (mouse_buttons[0] or keys[pygame.K_SPACE]) and can_fire:
            # check cooldown
            if current_time - self.last_torpedo_time >= self.torpedo_cooldown * 1000:
                self.launch_torpedo()
                self.last_torpedo_time = current_time

        # sonar activation (F)
        if keys[pygame.K_f]:
            self.activate_sonar()

    def move(self, dt):
        if self.is_dead:
            return # no movement while dead 
        
        if self.direction.length() > 0:
            self.hitbox_rect.x += self.direction.x * self.speed * dt
            self.collision('horizontal')
            self.hitbox_rect.y += self.direction.y * self.speed * dt
            self.collision('vertical')
            self.rect.center = self.hitbox_rect.center
            self.keep_within_bounds()
        self.update_animation(dt)

    def collision(self, direction):
            for sprite in self.collision_sprites:
                if self.hitbox_rect.colliderect(sprite.rect):
                    if direction == "horizontal":
                        if self.direction.x > 0:
                            self.hitbox_rect.right = min(self.hitbox_rect.right, sprite.rect.left)
                        elif self.direction.x < 0:
                            self.hitbox_rect.left = max(self.hitbox_rect.left, sprite.rect.right)
                    elif direction == "vertical":
                        if self.direction.y > 0:
                            self.hitbox_rect.bottom = min(self.hitbox_rect.bottom, sprite.rect.top)
                        elif self.direction.y < 0:
                            self.hitbox_rect.top = max(self.hitbox_rect.top, sprite.rect.bottom)
            self.rect.center = self.hitbox_rect.center

    def keep_within_bounds(self):
        self.hitbox_rect.left = max(WORLD_LEFT, self.hitbox_rect.left)
        self.hitbox_rect.right = min(WORLD_RIGHT, self.hitbox_rect.right)
        self.hitbox_rect.top = max(WORLD_TOP, self.hitbox_rect.top)
        self.hitbox_rect.bottom = min(WORLD_BOTTOM, self.hitbox_rect.bottom)
        if self.hitbox_rect.top < 795:
            self.hitbox_rect.top = 795
            self.hitbox_rect.bottom = self.hitbox_rect.top + self.rect.height
        self.rect.center = self.hitbox_rect.center

    # ===== COMBAT & ABILITIES =====
    def launch_torpedo(self,):
        """Launch torpedo toward mouse"""
        if self.is_dead: # can't launch torpedo while dead
            return 

        direction = self.aim_direction
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        direction = direction.normalize()

        torpedo = Torpedo(
            pos=self.rect.center,
            direction=direction,
            player_facing=self.last_horizontal,
            group=self.visible_sprites,
            collision_sprites=self.collision_sprites,
            explosion_frames=self.explosion_frames,
            explosion_group=self.explosion_group,
            monster_group=self.game_ref.enemy_sprites,
            obstacle_group=self.obstacle_group,
            visible_sprites=self.visible_sprites,
            game_ref=self.game_ref,
            damage=self.damage,
            owner=self
            )
        
        if self.game_ref and hasattr(self.game_ref, 'camera'):
            self.game_ref.camera.add(torpedo)

        # play sound
        # if self.game_ref and hasattr(self.game_ref, 'sounds'):
        #     self.game_ref.sounds['torpedo_launch'].play()

        if self.sounds.get('torpedo_launch'):
            self.sounds['torpedo_launch'].play()

        self.power -= self.torpedo_cost

    def activate_sonar(self):
        """Activate sonar pulse if conditions are met."""
        if self.is_dead: # Can't activate sonar while dead
            return False 
        
        current_time = pygame.time.get_ticks()
        
        # Check requirements
        if self.level < self.sonar_level_required:
            print(f"Sonar requires level {self.sonar_level_required}")
            return False
        
        if self.power < self.sonar_cost:
            print("Not enough power for sonar")
            return False
        
        # Check cooldown (convert milliseconds to seconds)
        time_since_last = (current_time - self.last_sonar_time) / 1000.0
        if time_since_last < self.sonar_cooldown:
            print(f"Sonar on cooldown: {self.sonar_cooldown - time_since_last:.1f}s remaining")
            return False
        
        # Activate sonar (removes fog and shows all monsters)
        self.sonar_active = True
        self.sonar_start_time = current_time
        self.power -= self.sonar_cost
        self.last_sonar_time = current_time

        # if self.game_ref and hasattr(self.game_ref, 'sounds'):
        #     self.game_ref.sounds['sonar_ping'].play()
        if self.sounds.get('sonar_ping'):
            self.sounds['sonar_ping'].play()
        
        return True
    
    def update_portal_detection(self, portal_group):
        """Update which portal the player can currently interact with."""
        closest_portal = None
        closest_distance = float('inf')

        for portal in portal_group:
            # calculate distance to portal
            player_pos = pygame.math.Vector2(self.rect.center)
            portal_pos = pygame.math.Vector2(portal.rect.center)
            distance = player_pos.distance_to(portal_pos)
            
            # check if this portal is the closest within interaction radius
            if distance < self.portal_interaction_radius and distance < closest_distance:
                closest_distance = distance
                closest_portal = portal
        
        # update current portal
        self.current_portal = closest_portal
        if self.current_portal:
            self.current_portal.is_current = True

    # ===== HEALTH AND POWER =====
    def take_damage(self, amount=1):
        if self.is_invincible or self.is_dead:
            return
        
        current = pygame.time.get_ticks()
        if current - self.last_hit_time > self.hit_cooldown:
            self.health -= amount
            self.is_hit = True
            self.hit_timer = 0.0
            self.last_hit_time = current
            self.last_damage_time = current

        if "damage" in self.sounds:
            self.sounds['damage'].play()

            if self.health <= 0:
                self.die()

    def regenerate_hp(self, dt):
        if self.is_dead or self.health >= self.max_health:
            return
        
        current_time = pygame.time.get_ticks()
        time_since_damage = (current_time - self.last_damage_time) / 1000.0

        # wait before regen
        if time_since_damage < HP_REGEN_DELAY:
            return
        
        self.health += self.hp_regen_rate * dt
        self.health = min(round(self.health), self.max_health)

    def power_regen(self, dt):
        self.power += self.power_regen_rate * dt
        self.power = min(self.power, self.max_power)

    # ===== xp & LEVELLING =====
    def add_xp(self, amount):
            if self.level >= self.max_level:
                return
            self.xp += amount

            while(
                self.level < self.max_level
                and self.xp >= self.xp_to_next[self.level]
            ):
                self.xp -= self.xp_to_next[self.level]
                self.level_up()

    def level_up(self):
        self.level += 1

        # damage scaling
        damage_step = (PLAYER_MAX_DAMAGE - PLAYER_BASE_DAMAGE) / (self.max_level - 1)
        self.damage = round(PLAYER_BASE_DAMAGE + damage_step * (self.level - 1))

        # cost reduction as level increases
        self.boost_cost = max(3, BOOST_COST - self.level * 0.4)
        self.torpedo_cost = max(5, TORPEDO_COST - self.level * 0.6)
        self.update_hp_regen_rate()

    def update_hp_regen_rate(self):
        """Handles HP regen rates based on level"""
        if self.level < HP_REGEN_LEVEL_REQUIRED:
            self.hp_regen_rate = 0
            return
        
        hp_regen_increment = round(
            (self.level - HP_REGEN_LEVEL_REQUIRED)
            / (self.max_level - HP_REGEN_LEVEL_REQUIRED)
        )
        self.hp_regen_rate = round(
            HP_REGEN_MIN
            + hp_regen_increment * (HP_REGEN_MAX - HP_REGEN_MIN)
        )

    # ===== DEATH & RESPAWN =====
    def die(self):
        """Handle player's death"""
        if not self.is_dead:
            self.is_dead = True
            self.health = 0
            self.image.set_alpha(100) # make semi-transparent
            print('Player Died!')

            if self.game_ref and hasattr(self.game_ref, 'player_respawn'):
                self.game_ref.player_respawn.start_respawn()

    def respawn(self, pos):
        """Respawn player at specific position"""
        self.is_dead = False 
        self.health = self.max_health
        self.power = self.max_power
        self.rect.center = pos
        self.hitbox_rect.center = pos

        self.start_invincibility()

    def start_invincibility(self):
        """Start invincibility after respawn"""
        self.is_invincible = True
        self.invincibility_timer = pygame.time.get_ticks()
        self.last_flash_time = pygame.time.get_ticks()
        self.flash_visible = True
        print("Invincible")

    def update_invincibility(self):
        """Update invincibility flashing effect"""
        if not self.is_invincible:
            self.image.set_alpha(255)
            return
        
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.invincibility_timer) / 1000.0
        
        # end invincibility after protection time
        if elapsed >= RESPAWN_PROTECTION_TIME:
            self.is_invincible = False
            self.image.set_alpha(255)
            print("Invinciblity ended")
            return
        
        # handles flashing effect
        flash_elapsed = current_time - self.last_flash_time
        if flash_elapsed >= RESPAWN_FLASH_INTERVAL:
            self.flash_visible = not self.flash_visible
            self.last_flash_time = current_time

            # apply flashing effect
            if self.flash_visible:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(100)

    # ===== ANIMATION & RENDERING =====
    def load_animation(self):
        self.animations = {}
        animation_folders = ['right', 'right_down', 'right_up', 'left', 'left_down', 'left_up']
        for folder in animation_folders:
            frames = []
            try:
                for i in range(4):
                    # frame_path = join('assets/images/player', folder, f'{i}.png')
                    frame_path = join(PLAYER_ASSETS, folder, f'{i}.png')
                    frame = pygame.image.load(frame_path).convert_alpha()
                    frames.append(frame)
                self.animations[folder] = frames
            except Exception as e:
                print(f"Warning: Could not load animation {folder}: {e}")
                frames = []
                for i in range(4):
                    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                    color = (0, 150, 255) if 'right' in folder else (100, 200, 255)
                    radius = 8 + (i * 2)
                    pygame.draw.rect(surf, color, (0, 0, 32, 32), border_radius=8)
                    pygame.draw.circle(surf, (255, 255, 255), (16, 16), radius)
                    frames.append(surf)
                self.animations[folder] = frames

    def update_animation(self, dt):
        if self.direction.length() == 0:
            target_animation = 'right' if self.last_horizontal == 'right' else 'left'
        else:
            if self.last_horizontal == 'right':
                if self.direction.y < 0:
                    target_animation = 'right_up'
                elif self.direction.y > 0:
                    target_animation = 'right_down'
                else:
                    target_animation = 'right'
            else:
                if self.direction.y < 0:
                    target_animation = 'left_up'
                elif self.direction.y > 0:
                    target_animation = 'left_down'
                else:
                    target_animation = 'left'
        if target_animation != self.current_animation:
            self.current_animation = target_animation
            self.animation_frame = 0
            self.animation_timer = 0
        if self.direction.length() > 0:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % len(self.animations[self.current_animation])
        else:
            self.animation_frame = 0
        self.image = self.animations[self.current_animation][self.animation_frame]

    def draw_trajectory(self, screen, camera_offset, dt):
        """Draw player crosshair line from player to mouse position"""
        self.update_mouse_aim(camera_offset) # to update mouse aim

        player_screen_pos = pygame.math.Vector2(self.rect.center) - camera_offset
        cross_screen_pos = self.crosshair_pos - camera_offset

        # crosshair line
        pygame.draw.line(screen,(CROSSHAIR_COLOR), 
                         player_screen_pos, 
                         cross_screen_pos, 2)
        # crosshair 
        pygame.draw.circle(screen, (CROSSHAIR_COLOR), cross_screen_pos, 6, 1)
        pygame.draw.circle(screen, (CROSSHAIR_COLOR), cross_screen_pos, 2)

    def update_mouse_aim(self, camera_offset):
        """Update crosshair position based on mouse cursor"""
        mouse_screen = pygame.mouse.get_pos()
        mouse_world = pygame.math.Vector2(mouse_screen) + camera_offset

        direction = mouse_world - pygame.math.Vector2(self.rect.center)
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)

        self.aim_direction = direction.normalize()
        self.crosshair_pos = (pygame.math.Vector2(self.rect.center
                + self.aim_direction * self.crosshair_length))

    # ===== UPDATE =====
    def update(self, dt):
        self.regenerate_hp(dt)
        self.power_regen(dt)

        if not self.is_dead:
            self.input(dt)
            self.move(dt)
            self.update_mouse_aim(pygame.math.Vector2(0, 0))

        if self.is_hit:
            self.hit_timer += dt
            alpha = 128 if (int(self.hit_timer * 10) % 2 == 0) else 255
            self.image.set_alpha(alpha)

            if self.hit_timer >= self.hit_flash_duration:
                self.is_hit = False
                self.image.set_alpha(255)

        # low health alert
        # if self.health <= 20 and not getattr(self, "low_health_alerted", False):
        #     if "low_health" in self.sounds:
        #         self.sounds["low_health"].play()
        #     self.low_health_aletered = True

        # if self.health > 20:
        #     self.low_health_aletered = False

        if self.health <= 20 and not getattr(self, "low_health_alerted", False):
            if self.sounds.get("low_health"):
                self.sounds["low_health"].play()
            self.low_health_alerted = True  # fix typo

        if self.health > 20:
            self.low_health_alerted = False

            
        self.update_invincibility()

        # sonar duration
        if self.sonar_active:
            elapsed = (pygame.time.get_ticks() - self.sonar_start_time) / 1000.0
            if elapsed >= self.sonar_duration:
                self.sonar_active = False
