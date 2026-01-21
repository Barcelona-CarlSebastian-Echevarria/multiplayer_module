import pygame
import os

from pytmx.util_pygame import load_pygame

from game.config import *

class MapSystem:
    """Handles all map-related functionality such as loading, rendering, and collisions"""
    
    def __init__(self):
        # tiled map data
        self.tmx_data = None  # TMX map data
        self.map_width = SCREEN_WIDTH * 3  # fallback: default width if map fails
        self.map_height = SCREEN_HEIGHT * 3  # fallback: default height if map fails

        # collision
        self.collision_sprites = pygame.sprite.Group()  # all collision objects

        # load & setup
        self.load_map()
        self.setup_collision()

        # map rendering (render once)
        self.map_surface = self.render_map_surface()

    # ===== MAP LOADING =====
    def load_map(self):
        """Load TMX map file and set map dimensions"""
        try:
            self.tmx_data = load_pygame(MAP_PATH)
            # Set map dimensions in pixels
            self.map_width = self.tmx_data.width * self.tmx_data.tilewidth
            self.map_height = self.tmx_data.height * self.tmx_data.tileheight

            print(f"Map loaded: {self.map_width}x{self.map_height}")
        except Exception:
            self.tmx_data = None

    # ===== MAP RENDERING =====
    def render_map_surface(self):
        """Render the entire map once"""
        if not self.tmx_data:
            return self.create_simple_background()
        
        map_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)

        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        map_surface.blit(tile, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))
        return map_surface
    
    def get_map_surface(self):
        """Render entire map to a single surface for fast blitting"""
        if not self.tmx_data:
            return self.create_simple_background()  # fallback surface

        map_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)

        # render visible tile layers only
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'data'):
                tile_count = 0

                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        map_surface.blit(tile, (x * TILE_SIZE, y * TILE_SIZE))
                        tile_count += 1

        print("Map rendering complete!")
        return map_surface
    
    # ===== COLLISION SETUP =====
    def setup_collision(self):
        """Create collision sprites from Object Layer 1"""

        from game.collision import CollisionSprite

        if not self.tmx_data:
            self.create_border_walls()
            return

        try:
            collision_layer = self.tmx_data.get_layer_by_name("Object Layer 1")
        except Exception:
            self.create_border_walls()
            return

        collision_count = 0
        for obj in collision_layer:
            # only process rectangular objects
            if hasattr(obj, "x") and hasattr(obj, "y") and hasattr(obj, "width") and hasattr(obj, "height"):
                CollisionSprite(
                    pos=(obj.x, obj.y),
                    size=(obj.width, obj.height),
                    groups=[self.collision_sprites]
                )
                collision_count += 1

        # always create border walls
        self.create_border_walls()
    
    def create_border_walls(self):
        """Create invisible walls around map edges to prevent leaving map"""
        border = 50  # thickness of walls
        from game.collision import CollisionSprite

        # top
        CollisionSprite((0, -border), (self.map_width, border), [self.collision_sprites])
        # bottom
        CollisionSprite((0, self.map_height), (self.map_width, border), [self.collision_sprites])
        # left
        CollisionSprite((-border, 0), (border, self.map_height), [self.collision_sprites])
        # right
        CollisionSprite((self.map_width, 0), (border, self.map_height), [self.collision_sprites])
    
    # ===== FALLBACK BACKGROUND =====
    def create_simple_background(self):
        """Fallback background if TMX map fails: ocean gradient"""
        print("Creating simple background...")
        background = pygame.Surface((self.map_width, self.map_height))

        # draw gradient by lines for performance
        for y in range(0, self.map_height, 4):
            depth = y / self.map_height  # 0.0 top -> 1.0 bottom
            blue = 50 + int(100 * depth)
            green = 30 + int(30 * depth)
            pygame.draw.line(background, (0, green, blue), (0, y), (self.map_width, y), 4)

        return background
