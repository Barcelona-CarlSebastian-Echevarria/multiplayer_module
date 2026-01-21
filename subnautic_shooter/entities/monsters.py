# entities/monsters.py
import pygame
import os
from random import randint, choice
from game.config import *
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Monster(pygame.sprite.Sprite):
    """Enemy AI with different AI behaviors and animations"""

    def __init__(
            self, 
            pos, 
            groups, 
            collision_sprites, 
            map_collision_sprites, 
            player=None, 
            enemy_type='fly'
    ):
        super().__init__(*groups)

        # references
        self.player = player
        self.collision_sprites = collision_sprites
        self.map_collision_sprites = map_collision_sprites
        self.enemy_type = enemy_type

        if enemy_type in MONSTER_TYPES:
            data = MONSTER_TYPES[enemy_type]
        else:
            data = MONSTER_TYPES["fly"] # fallback

        # monster stats
        self.size = data.get("size", (40, 40))
        self.health = data["hp"]
        self.max_health = self.health
        self.speed = randint(*data["speed"])
        self.damage = data.get("damage", 10)
        self.xp_reward = data.get("xp", 10)
        self.frames_count = data.get("frames", 1)
        self.alive = True

        # load animations
        self.animations = self.load_animations(enemy_type)
        self.direction_facing = "right"
        self.current_frame = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.4

        self.base_image = self.animations[self.direction_facing][0]
        self.image = self.base_image.copy()

        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.create_hitbox()

        self.alpha = 255
        self.z_layer = 3

        # movement & AI
        self.direction = self.random_direction()
        self.state = "wander"
        self.change_dir_timer = 0.0
        self.attack_cooldown = 0.0

    # ===== SETUP HELPERS =====
    def load_animations(self, enemy_type):
        animations = {"left": [], "right": []}

        colors = {
            "angler_fish": (255, 150, 50),
            "lamprey": (100, 100, 255),
            "squid": (150, 50, 150),
            "sword_fish": (255, 200, 50),
            "fly": (255, 100, 100),
        }

        for direction in ["left", "right"]:
            for i in range(self.frames_count):
                path = f"{MONSTERS_PATH}/{enemy_type}/{direction}/{i}.png"
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, self.size)

                except Exception:
                    # ✅ fallback ONLY if image fails
                    img = pygame.Surface(self.size, pygame.SRCALPHA)
                    color = colors.get(enemy_type, (255, 100, 100))
                    pygame.draw.ellipse(img, color, img.get_rect())

                    eye_size = max(3, self.size[0] // 10)
                    pygame.draw.circle(
                        img,
                        (255, 255, 255),
                        (self.size[0] // 3, self.size[1] // 3),
                        eye_size,
                    )

                animations[direction].append(img)

        return animations
            
    def create_hitbox(self):
        margin_x = int(self.size[0] * 0.2)
        margin_y = int(self.size[1] * 0.2)
        return self.rect.inflate(-margin_x, -margin_y)

    def random_direction(self):
        direction = pygame.math.Vector2(
            randint(-1, 1),
            randint(-1, 1)
        )
        return direction.normalize() if direction.length() else direction

    # ===== AI BEHAVIORS =====
    def wander(self, dt):
        self.change_dir_timer += dt
        if self.change_dir_timer >= 2.0:
            self.direction = self.random_direction()
            self.change_dir_timer = 0.0

    def chase(self, target_pos):
        direction = target_pos - pygame.math.Vector2(self.rect.center)
        if direction.length():
            self.direction = direction.normalize()

    def update_state(self, distance):
        if distance <= DETECTION_RANGE:
            self.state = "chase"
        elif distance >= LOSE_INTEREST_RANGE:
            self.state = "wander"

    # ===== MOVEMENT AND COLLISIONS =====
    def move(self, dt):
        if not self.direction.length():
            return
        
        movement = self.direction * self.speed * dt

        self.axis_move(movement.x, 0)
        self.axis_move(0, movement.y)

        self.keep_within_bounds()

        if self.player and self.hitbox_rect.colliderect(self.player.hitbox_rect):
            repulsion = pygame.math.Vector2(self.hitbox_rect.center) - pygame.math.Vector2(self.player.hitbox_rect.center)
            if repulsion.length():
                self.hitbox_rect.center += repulsion.normalize() * 2  # repulsion strength (adjustable)
                self.rect.center = self.hitbox_rect.center

        self.rect.center = self.hitbox_rect.center

    def axis_move(self, dx, dy):
        self.hitbox_rect.x += dx
        self.hitbox_rect.y += dy

        for sprite in self.map_collision_sprites:
            if self.hitbox_rect.colliderect(sprite.rect):
                if dx > 0:
                    self.hitbox_rect.right = sprite.rect.left
                elif dx < 0:
                    self.hitbox_rect.left = sprite.rect.right
                if dy > 0:
                    self.hitbox_rect.bottom = sprite.rect.top
                elif dy < 0:
                    self.hitbox_rect.top = sprite.rect.bottom

    def keep_within_bounds(self):
        self.hitbox_rect.left = max(WORLD_LEFT, self.hitbox_rect.left)
        self.hitbox_rect.right = min(WORLD_RIGHT, self.hitbox_rect.right)
        self.hitbox_rect.top = max(WORLD_TOP, self.hitbox_rect.top)
        self.hitbox_rect.bottom = min(WORLD_BOTTOM, self.hitbox_rect.bottom)

        if self.hitbox_rect.top < 795:
            self.hitbox_rect.top = 795

    # ===== COMBAT & VISIBILITY =====
    def update_visibility(self, distance):
        if self.player and getattr(self.player, "sonar_active", False):
            if distance <= self.player.sonar_range:
                self.set_alpha(255)
                return

        if distance <= VISIBILITY_RADIUS:
            alpha = 255
        elif distance >= FOG_RADIUS:
            alpha = 0
        else:
            ratio = 1 - (distance - VISIBILITY_RADIUS) / (FOG_RADIUS - VISIBILITY_RADIUS)
            alpha = int(255 * ratio)

        self.set_alpha(alpha)

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.image = self.base_image.copy()
        self.image.set_alpha(self.alpha)

    def take_damage(self, amount):
        self.health -= amount

        if self.health <= 0 and self.alive:
            self.alive = False
            return self.xp_reward
        return 0
    
    # ===== ANIMATION =====
    def update_animation(self, dt):
        if self.direction.x < 0:
            self.direction_facing = "left"
        elif self.direction.x > 0:
            self.direction_facing = "right"

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.direction_facing])
            self.animation_timer = 0.0

        self.base_image = self.animations[self.direction_facing][self.current_frame]
        self.image = self.base_image.copy()
        self.image.set_alpha(self.alpha)

    # ===== UPDATE =====
    def update(self, dt):
        if not self.alive:
            self.kill()
            return

        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        player_pos = pygame.math.Vector2(self.player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        distance = player_pos.distance_to(enemy_pos)

        self.update_state(distance)

        if self.player.is_invincible or self.player.is_dead:
            self.wander(dt)
        elif self.state == "wander":
            self.wander(dt)
        elif self.state == "chase":
            self.chase(player_pos)

        self.update_visibility(distance)
        self.move(dt)
        self.keep_within_bounds()

        if (
            not self.player.is_dead
            and not self.player.is_invincible
            and self.hitbox_rect.colliderect(self.player.hitbox_rect)
            and self.attack_cooldown <= 0
        ):
            
            if self.hitbox_rect.colliderect(self.player.hitbox_rect) and self.attack_cooldown <= 0:
                self.player.take_damage(self.damage)
                self.attack_cooldown = 1.0

                # push monsters away
                push_vector = pygame.math.Vector2(self.hitbox_rect.center) - pygame.math.Vector2(self.player.hitbox_rect.center)
                if push_vector.length() == 0:
                    push_vector = pygame.math.Vector2(randint(-1,1), randint(-1,1))
                push_vector = push_vector.normalize() * 20 # push/knockback strength (adjustable)
                self.hitbox_rect.center += push_vector
                self.rect.center = self.hitbox_rect.center

        self.update_animation(dt)

        self.rect.center = self.hitbox_rect.center
