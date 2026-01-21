# entities/camera.py
import pygame

class Camera(pygame.sprite.Group):
    """Manages viewport and sprite render with offset"""
    def __init__(self, screen, map_width, map_height):
        super().__init__()
        self.surface = screen
        self.offset = pygame.math.Vector2()
        self.map_width = map_width
        self.map_height = map_height
        self.screen_width, self.screen_height = screen.get_size()
    
    def centered_player_cam(self, target):
        """Center camera on player"""
        target_x = target.rect.centerx - self.screen_width // 2
        target_y = target.rect.centery - self.screen_height // 2
        
        # keep camera within map bounds
        self.offset.x = max(0, min(target_x, self.map_width - self.screen_width))
        self.offset.y = max(0, min(target_y, self.map_height - self.screen_height))
    
    def custom_draw(self, player):
        """Draw all sprites with camera offset, sorted by z-layer"""
        # sort sprites by z-layer and y-position
        self_sprites = sorted(self.sprites(), 
                               key=lambda sprite: (getattr(sprite, 'z_layer', 0), 
                                                  sprite.rect.centery))
        
        for sprite in self_sprites:
            offset_pos = pygame.math.Vector2(sprite.rect.topleft) - self.offset
            self.surface.blit(sprite.image, (offset_pos.x, offset_pos.y))