# This is the main game loop for Subnautic Shooter (Single Player Mode)

import pygame
import os
import sys

# Get the current directory 
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
parent_dir = os.path.dirname(current_dir)
# Add parent directory to Python path
sys.path.insert(0, parent_dir)

from game.config import *
from game.gamestate import GameState

class Game:
    def __init__(self):
        # ===== PYGAME SETUP =====
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Subnautic Shooter")
        self.clock = pygame.time.Clock()
        self.running = True

        # ===== SPRITE GROUPS =====
        self.collision_sprites = pygame.sprite.Group()
        self.obstacle_group = pygame.sprite.Group()
        self.visible_sprites = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()

        # ===== MAP SETTINGS =====
        self.map_width = SCREEN_WIDTH * 3
        self.map_height = SCREEN_HEIGHT * 3

        # ===== GAME STATE =====
        self.gamestate = GameState(
            screen = self.screen,
            collision_sprites=self.collision_sprites,
            obstacle_group=self.obstacle_group,
            visible_sprites=self.visible_sprites,
            explosion_group=self.explosion_group
        )

    # def run(self):
    #     while self.running:
    #         dt = self.clock.tick(FPS) / 1000  # Delta time in seconds

    #         for event in pygame.event.get():
    #             if event.type == pygame.QUIT:
    #                 self.running = False

    #         self.gamestate.update(dt)

    #         self.screen.fill((0, 0, 0))  # clear screen
            
    #         self.gamestate.draw(self.screen)

    #         pygame.display.flip()

    #     pygame.quit()

    def update(self, events, dt):
        for event in events:
            if event.type == pygame.QUIT:
                return ("QUIT", None)
        self.gamestate.update(dt)
        return None

    def draw(self, screen):
        screen.fill((0, 0, 0))
        self.gamestate.draw(screen)

def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()