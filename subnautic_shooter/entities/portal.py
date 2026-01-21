# entities/portal.py
import pygame
from os.path import join
from game.config import *

portal_network_created = False
existing_portal_group = None


class PortalNode:
    """Represents a portal in the network."""
    def __init__(self, position, portal_index):
        self.position = pygame.math.Vector2(position)
        self.portal_index = portal_index
        self.next = None
        self.prev = None


class Portal(pygame.sprite.Sprite):
    """Portal sprite with animation and teleport logic."""
    def __init__(self, node, visible_sprites, portal_group, camera, game_ref):
        super().__init__(visible_sprites, portal_group)
        self.node = node
        self.game_ref = game_ref

        # Get portal size from PORTAL_NODES
        left, top, right, bottom = PORTAL_NODES[node.portal_index]
        width = right - left
        height = bottom - top

        # Load portal frames
        self.frames = []
        for i in range(6):
            try:
                frame = pygame.image.load(join(PORTAL_PATH, f'{i}.png')).convert_alpha()
                frame = pygame.transform.scale(frame, (width, height))
            except:
                frame = pygame.Surface((width, height), pygame.SRCALPHA)
                color = [(150, 50, 250), (50, 150, 250), (250, 50, 150), (50, 250, 150)][node.portal_index % 4]
                pygame.draw.ellipse(frame, (*color, 200), (0, 0, width, height))
                pygame.draw.ellipse(frame, (*color, 100), (10, 10, width - 20, height - 20))
            self.frames.append(frame)

        self.frame_index = 0
        self.animation_speed = 0.15
        self.animation_timer = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=node.position)

        camera.add(self)

    # ===== ANIMATION =====
    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

    # ===== TELEPORTATION =====
    def try_teleport(self, player, direction, current_time):
        """Teleport player to linked portal (next or prev)."""
        if current_time - player.last_portal_time < PORTAL_COOLDOWN:
            return False

        target_node = self.node.next if direction == "next" else self.node.prev
        if not target_node:
            return False

        old_pos = player.rect.center
        player.rect.center = target_node.position
        player.hitbox_rect.center = target_node.position
        player.last_hit_time = current_time
        player.last_portal_time = current_time

        if player.game_ref and hasattr(player.game_ref, 'sounds'):
            if 'teleport' in player.game_ref.sounds:
                player.game_ref.sounds['teleport'].play()

        return True

    # ===== DRAW =====
    def draw(self, screen, camera_offset):
        """Draw portal sprite with camera offset."""
        pos = pygame.math.Vector2(self.rect.topleft) - camera_offset
        screen.blit(self.image, pos)

        if getattr(self, "is_current", False):
            icon_color = (0,255,0)
            pygame.draw.circle(screen, icon_color, pos + pygame.math.Vector2(self.rect.width/2, self.rect.height/2), 10)


# ===== PORTAL NETWORK =====
def create_portal_network(visible_sprites, camera, game_ref):
    """Create circular doubly-linked portal network with sprites."""
    global portal_network_created, existing_portal_group

    if portal_network_created and existing_portal_group:
        return existing_portal_group

    portal_group = pygame.sprite.Group()
    nodes = []

    # Create nodes
    for i, rect in enumerate(PORTAL_NODES):
        left, top, right, bottom = rect
        center = (left + (right - left) // 2, top + (bottom - top) // 2)
        nodes.append(PortalNode(center, i))

    # Link nodes circularly
    for i, node in enumerate(nodes):
        node.next = nodes[(i + 1) % len(nodes)]
        node.prev = nodes[(i - 1) % len(nodes)]

    # Create portal sprites
    for node in nodes:
        Portal(node, visible_sprites, portal_group, camera, game_ref)

    portal_network_created = True
    existing_portal_group = portal_group
    return portal_group


# ===== PORTAL COLLISIONS =====
def check_portal_collisions(portal_group, player, current_time):
    """Check if player can teleport through nearby portals."""
    player.update_portal_detection(portal_group)
    if not player.current_portal:
        return

    keys = pygame.key.get_pressed()
    if keys[pygame.K_e]:
        player.current_portal.try_teleport(player, "next", current_time)
    elif keys[pygame.K_q]:
        player.current_portal.try_teleport(player, "prev", current_time)
