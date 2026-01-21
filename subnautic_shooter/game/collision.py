# game/collision.py
import pygame

class Tile(pygame.sprite.Sprite):
    """Simple tile sprite"""
    def __init__(self, pos, surf, groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.z_layer = 0


class CollisionSprite(pygame.sprite.Sprite):
    """Invisible collision sprite"""
    def __init__(self, pos, size, groups):
        super().__init__(*groups)
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.image = pygame.Surface((size[0], size[1]), pygame.SRCALPHA)
