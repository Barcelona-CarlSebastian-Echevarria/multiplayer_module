# This is app.py - Main application file to run the game

import pygame
from game_pages.start_menu import StartMenu
from utils.stack import Stack

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.clock = pygame.time.Clock()

        # Stack ADT for scene management
        self.scenes = Stack()
        self.scenes.push(StartMenu())

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            current = self.scenes.peek()
            dt = self.clock.tick(60) / 1000

            result = current.update(events, dt)
            current.draw(self.screen)
            pygame.display.flip()

            if result:
                action, payload = result

                if action == "PUSH":
                    self.scenes.push(payload)

                elif action == "POP":
                    self.scenes.pop()

                elif action == "REPLACE":
                    self.scenes.pop()
                    self.scenes.push(payload)

                elif action == "QUIT":
                    running = False

            self.screen.fill((0, 0, 0))
            current.draw(self.screen)
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    game = Main()
    game.run()
