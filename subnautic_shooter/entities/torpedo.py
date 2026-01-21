# entities/torpedo.py
import os
import pygame
from os.path import join
import math
from game.config import *
from entities.explosion import AnimatedExplosion

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

class Torpedo(pygame.sprite.Sprite):
    """Handles torpedo movement states, animation, trigger explosion animation, collision detection"""

    def __init__(
        self,
        pos,
        direction,
        player_facing,
        group,
        collision_sprites,
        explosion_frames,
        explosion_group,
        monster_group,
        obstacle_group,
        visible_sprites,
        game_ref,
        damage,
        owner
    ):
        super().__init__(group)
        self.monster_group = monster_group
        self.owner = owner

        # store player's facing direction
        self.player_facing = player_facing

        #store mouse direction
        self.target_direction = direction.normalize()

        # initial drop direction(purely horizontal based on player facing)
        self.drop_direction = pygame.math.Vector2(-1,0) if player_facing == 'left' else pygame.math.Vector2(1,0)

        # current direction starts as drop direction
        self.current_direction = self.drop_direction.copy()
        self.direction = self.drop_direction.copy()

        sound_folder = os.path.join(PROJECT_ROOT, "subnautic_shooter", "assets", "audio", "sound_effects")

        self.sounds = {
            'torpedo_hit': pygame.mixer.Sound(os.path.join(sound_folder, "projectile_hit.mp3"))
        }

        # load frames based on direction
        if player_facing == 'left':
            torpedo_folder = RIGHT_TORPEDO_PATH
            self.image_facing_left = True
        else:
            torpedo_folder = LEFT_TORPEDO_PATH
            self.image_facing_left = False
        
        # load frames
        self.frames = []
        for i in range(5):
            try:
                frame = pygame.image.load(
                    join(torpedo_folder, f'{i}.png')
                ).convert_alpha()
                self.frames.append(frame)
            except Exception as e:
                print(f"Error loading torpedo frame {i}: {e}")
                frame = pygame.Surface((20, 8), pygame.SRCALPHA)
                pygame.draw.rect(frame, (50, 150, 200), (0, 0, 20, 8))
                pygame.draw.rect(frame, (100, 200, 255), (2, 2, 16, 4))
                self.frames.append(frame)
                
        # preserve original frames for rotation
        self.original_frames = []
        for frame in self.frames:
            self.original_frames.append(frame.copy())

        # movement states
        self.state = 'dropping'
        self.state_timer = 0
        self.drop_duration = TORPEDO_DROP_DURATION
        self.float_duration = TORPEDO_FLOAT_DURATION
        self.accel_duration = TORPEDO_ACCEL_DURATION
        self.drop_speed = TORPEDO_DROP_SPEED
        self.float_speed = TORPEDO_FLOAT_SPEED
        self.max_speed = TORPEDO_SPEED
        self.acceleration = TORPEDO_ACCELERATION

        # damage
        self.damage = damage
        self.torpedo_damage_radius = TORPEDO_DAMAGE_RADIUS
        
        # collision & effects
        self.collision_sprites = collision_sprites
        self.obstacle_group = obstacle_group
        self.explosion_frames = explosion_frames
        self.explosion_group = explosion_group
        self.visible_sprites = visible_sprites
        self.game_ref = game_ref

        # movement & physics
        self.pos = pygame.math.Vector2(pos)  # must be first
        self.velocity = pygame.math.Vector2(0, 0)
        self.gravity = pygame.math.Vector2(0, 0.15)
        self.drag = 0.995

        # Animation control
        self.frame_index = 0
        self.animation_speed = 0.2
        self.animation_timer = 0

        # initial frame setup
        self.image = self.get_current_frame()  # uses self.pos internally
        self.rect = self.image.get_rect(center=self.pos)

        # state & collision flags
        self.state = 'dropping'
        self.state_timer = 0
        self.alive = True
        self.has_hit_something = False
        self.z_layer = 2

    # ===== ANIMATIONS =====
    def get_current_frame(self):
        frame = self.original_frames[int(self.frame_index)]
        
        if self.current_direction.length() > 0:
            # calculate the angle in radians first
            angle_rad = math.atan2(self.current_direction.y, self.current_direction.x)
            # convert to degrees (pygame uses degrees for rotation)
            angle_deg = math.degrees(angle_rad)
            
            # handle left-facing sprites differently
            if not self.image_facing_left:  # Original sprite faces left
                # for left-facing sprites, they're already 180 degrees rotated
                angle_deg += 180
            
        else:
            angle_deg = 0
        
        rotated_frame = pygame.transform.rotate(frame, -angle_deg)
        return rotated_frame

    def create_explosion(self):
        """Spawn explosion animation at impact point."""
        AnimatedExplosion(
            self.explosion_frames,
            self.rect.center,
            [self.explosion_group, self.visible_sprites]
        )

    # ===== TORPEDO MOVEMENT =====
    def update_state(self, dt):
        """Handle movement logic based on the torpedo's current state with true 2D motion."""
        if self.has_hit_something:
            return
            
        self.state_timer += dt
        
        # advance animation frames
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
        
        # DROPPING STATE
        if self.state == 'dropping':
            self.velocity = self.drop_direction * self.drop_speed
            self.velocity += self.gravity * dt
            self.current_direction = self.drop_direction  # For rotation
            
            if self.state_timer >= self.drop_duration:
                self.state = 'floating'
                self.state_timer = 0

        # FLOATING STATE  
        elif self.state == 'floating':
            # spherical linear interpolation (slerp) for smooth rotation
            t = min(self.state_timer / self.float_duration, 1.0)
            
            # normalize both vectors
            start = self.drop_direction.normalize()
            end = self.target_direction.normalize()
            
            # calculate angle between vectors
            dot = start.dot(end)
            dot = max(-1, min(1, dot))  # Clamp
            angle = math.acos(dot)
            
            if angle < 0.001:  # too close, use end direction
                self.current_direction = end
            else:
                # spherical interpolation
                self.current_direction = (math.sin((1 - t) * angle) * start + 
                                        math.sin(t * angle) * end) / math.sin(angle)
                                    
            # ,ove in current direction
            self.velocity = self.current_direction * self.float_speed
            
            # add sine wave effect
            perpendicular = pygame.math.Vector2(-self.current_direction.y, self.current_direction.x)
            self.velocity += perpendicular * math.sin(self.state_timer * 8) * (self.float_speed * 0.5)
            self.velocity += self.gravity * dt * 0.5
            self.velocity *= self.drag
            
            if self.state_timer >= self.float_duration:
                self.state = 'accelerating'
                self.state_timer = 0

        # ACCELERATING STATE
        elif self.state == 'accelerating':
            # use target_direction(mouse), not self.direction
            self.current_direction = self.target_direction
            
            # accelerate in target direction
            self.velocity += self.target_direction * self.acceleration * dt
            self.velocity += self.gravity * dt
            self.velocity *= self.drag
            
            if self.velocity.length() > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed
                
            if self.state_timer >= self.accel_duration:
                self.state = 'active'

        # ACTIVE STATE  
        elif self.state == 'active':
            # continue in target direction
            if self.velocity.length() < self.max_speed:
                self.velocity += self.target_direction * self.acceleration * 0.5 * dt
            self.velocity += self.gravity * dt
            self.velocity *= self.drag
            
            if self.velocity.length() < self.max_speed * 0.7:
                self.velocity = self.target_direction * self.max_speed * 0.7
    
        # if self.velocity.length() > 0:
        #     self.direction = self.velocity.normalize()

    # ===== CHECK COLLISIONS (WALLS & MONSTERS) =====
    def check_collision(self):
        """Detect collision with enemies or environment."""
        if self.has_hit_something:
            return False
        
        torpedo_center = pygame.math.Vector2(self.rect.center)
        hit_any = False

        # monster splash damage
        if hasattr(self, 'monster_group') and self.monster_group:
            for monster in self.monster_group:
                monster_center = pygame.math.Vector2(monster.rect.center)
                distance = torpedo_center.distance_to(monster_center)

                if distance <= self.torpedo_damage_radius:
                    # apply damdage and get xp
                    xp = monster.take_damage(self.damage)
                    if xp > 0 and self.owner:
                        self.owner.add_xp(xp)
                    hit_any = True
        
        # check wall collision
        if hasattr(self, 'collision_sprites'):
            hitbox = self.rect.inflate(-15, -15) 
            
            for sprite in self.collision_sprites:
                if hasattr(sprite, 'rect') and hitbox.colliderect(sprite.rect):
                    self.create_explosion()
                    self.has_hit_something = True
                    self.velocity.update(0, 0)
                    # if self.game_ref and hasattr(self.game_ref, 'sounds'):
                    #     self.game_ref.sounds['torpedo_hit'].play()
                    if self.sounds.get('torpedo_hit'):
                        self.sounds['torpedo_hit'].play()
                    return True
        
        # check obstacle collisions
        if hasattr(self, 'obstacle_group') and self.obstacle_group:
            obstacle_hits = pygame.sprite.spritecollide(self, self.obstacle_group, False)
            if obstacle_hits:
                self.create_explosion()
                self.has_hit_something = True
                self.velocity.update(0, 0)
                # if self.game_ref and hasattr(self.game_ref, 'sounds'):
                #     self.game_ref.sounds['torpedo_hit'].play()
                if self.sounds.get('torpedo_hit'):
                    self.sounds['torpedo_hit'].play()
                return True
        
        # handle hit
        if hit_any:
            self.has_hit_something = True
            self.create_explosion()
            self.velocity.update(0, 0)
            if self.sounds.get('torpedo_hit'):
                self.sounds['torpedo_hit'].play()
            return True

        return False

    def update(self, dt):
        if not self.alive:
            self.kill()
            return
            
        # update movement and animation    
        self.update_state(dt)
        self.pos += self.velocity * dt
        
        # update image based on current frame and rotation
        self.image = self.get_current_frame()
        self.rect = self.image.get_rect(center=self.pos)

        if self.check_collision():
            self.alive = False
            self.kill()
            return
        
        # cleanup if far outside world bounds
        if (self.rect.right < WORLD_LEFT or
            self.rect.left > WORLD_RIGHT or
            self.rect.bottom < -3520 or
            self.rect.top > WORLD_BOTTOM):
            self.kill()