# entities/explosion.py
import pygame

class AnimatedExplosion(pygame.sprite.Sprite):
    """Plays Explosion animation and deletes after"""

    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[0].copy()
        self.rect = self.image.get_rect(center=pos)
        self.z_layer = 5
        self.animation_speed = 15  # frames per second
        self.frame_timer = 0

    def update(self, dt):
        """Animate explosion frame by frame and remove when done."""
        self.frame_timer += dt
        if self.frame_timer >= 1.0 / self.animation_speed:
            self.frame_timer = 0
            self.frame_index += 1
            if self.frame_index >= len(self.frames): # check if animation is complete
                self.kill()
                return
            self.image = self.frames[self.frame_index] # update to next frame
