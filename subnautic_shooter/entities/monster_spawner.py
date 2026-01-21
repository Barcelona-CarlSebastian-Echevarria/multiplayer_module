# entities/monster_spawner.py
import pygame
from random import randint, choice
from game.config import *
from entities.monsters import Monster

class MonsterSpawner:
    """Continuously spawns monsters with difficulty scaling over time."""

    def __init__(
        self,
        player,
        enemy_sprites,
        visible_sprites,
        collision_sprites,
        map_collision_sprites
    ):
        # references
        self.player = player
        self.enemy_sprites = enemy_sprites
        self.visible_sprites = visible_sprites
        self.collision_sprites = collision_sprites
        self.map_collision_sprites = map_collision_sprites

        # timing
        self.spawn_interval = MONSTER_SPAWN_INTERVAL
        self.timer = 0.0
        self.game_time = 0.0 # total elapsed time (seconds)

        # fixed spawn amount per wave
        self.base_spawn_count = MONSTER_SPAWN_RATIO.copy()
    
        # difficulty scaling
        self.difficulty_scale = 1.0
        self.difficulty_increase_interval = 60 # increase difficulty every 2 mins
        self.last_difficulty_tick = 0

        # spawn tracking
        self.wave_number = 0

        # spawn initial monsters immediately
        self.spawn_initial_batch()

    def spawn_initial_batch(self):
        """Spawn initial fixed amount of monsters"""
        for monster_type, data in MONSTER_SPAWN_AREA.items():
            for i in range(data["count"]):
                self.spawn_monster(monster_type)

    def spawn_wave(self):
        """Spawn a scaled number of monsters"""
        self.wave_number += 1

        for monster_type, base_count in self.base_spawn_count.items():
            scaled_count = max(1, int(base_count * self.difficulty_scale))

            for i in range(scaled_count):
                self.spawn_monster(monster_type)

    def spawn_monster(self, monster_type):
        """Spawn monsters in designated spawn areas"""
        spawn_data = MONSTER_SPAWN_AREA[monster_type]

        area = choice(spawn_data["areas"]) # generates random position
        x1, y1, x2, y2 = area

        x = randint(min(x1, x2), max(x1, x2))
        y = randint(min(y1, y2), max(y1, y2))

        # create monsters
        monster = Monster(
            pos=(x, y),
            groups=[self.visible_sprites, self.enemy_sprites],
            collision_sprites=self.collision_sprites,
            map_collision_sprites=self.map_collision_sprites,
            player=self.player,
            enemy_type=monster_type
        )
        if hasattr(self.player, 'game_ref') and hasattr(self.player.game_ref, 'camera'):
            self.player.game_ref.camera.add(monster)

    def increase_difficulty(self):
        """Increases monster count over time"""
        self.difficulty_scale += MONSTER_COUNT_DIFFICULTY_SCALE

    def update(self, dt):
        self.timer += dt
        self.game_time += dt

        if self.game_time - self.last_difficulty_tick >= self.difficulty_increase_interval:
            self.increase_difficulty()
            self.last_difficulty_tick = self.game_time
    
        if self.timer >= self.spawn_interval:
            self.spawn_wave()
            self.timer = 0