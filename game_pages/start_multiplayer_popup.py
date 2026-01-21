# This is the multiplayer popup for selecting ranked or lobby

import pygame
import os
import sys

class MultiplayerPopup:
    def __init__(self, screen_width, screen_height, on_ranked=None, on_lobby=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.visible = False
        
        # Callbacks
        self.on_ranked = on_ranked
        self.on_lobby = on_lobby
        
        # Popup rectangle - made taller
        self.rect = pygame.Rect(screen_width//2 - 300, screen_height//2 - 150, 600, 350)
        
        # Button rectangles - properly centered and spaced
        button_width = 240
        button_height = 140
        button_y = self.rect.y + 110
        button_spacing = 20
        
        left_button_x = self.rect.x + (self.rect.width//2 - button_width - button_spacing//2)
        right_button_x = self.rect.x + (self.rect.width//2 + button_spacing//2)
        
        self.ranked_button = pygame.Rect(left_button_x, button_y, button_width, button_height)
        self.lobby_button = pygame.Rect(right_button_x, button_y, button_width, button_height)
        
        # Smaller close button in better position - moved left and adjusted
        self.close_button = pygame.Rect(self.rect.right - 40, self.rect.y + 20, 30, 30)
        
        # Colors
        self.RANKED_COLOR = (30, 100, 200)      # Blue
        self.RANKED_HOVER = (50, 130, 230)
        self.LOBBY_COLOR = (30, 150, 80)        # Green
        self.LOBBY_HOVER = (50, 180, 110)
        self.POPUP_BG = (40, 40, 50)
        self.CLOSE_COLOR = (180, 60, 60)
        self.CLOSE_HOVER = (200, 80, 80)
        self.LIGHT = (200, 200, 200)
        self.DARK = (0, 0, 0)
        self.SHADOW = (0, 0, 0)
        self.BORDER = (100, 100, 100)
    
    def show(self):
        self.visible = True
    
    def hide(self):
        self.visible = False
    
    def draw(self, screen, font_small, font_medium, font_large):
        if not self.visible:
            return
        
        # Get mouse position for hover effects
        mx, my = pygame.mouse.get_pos()
        
        # Draw popup background with shadow
        pygame.draw.rect(screen, (20, 20, 20), self.rect.move(4, 4))
        pygame.draw.rect(screen, self.POPUP_BG, self.rect)
        pygame.draw.rect(screen, self.BORDER, self.rect, 3)
        
        # Draw title (centered, moved down)
        title_text = "MULTIPLAYER MODE"
        title_surface = font_large.render(title_text, True, self.LIGHT)
        title_x = self.rect.x + (self.rect.width - title_surface.get_width()) // 2
        title_y = self.rect.y + 50
        screen.blit(title_surface, (title_x, title_y))
        
        # Draw close button with hover effect
        close_color = self.CLOSE_HOVER if self.close_button.collidepoint(mx, my) else self.CLOSE_COLOR
        pygame.draw.rect(screen, close_color, self.close_button)
        
        # Draw X with smaller font that fits better
        close_text_font = pygame.font.Font(None, 24)  # Smaller font for X
        close_text = close_text_font.render("X", True, (255, 255, 255))
        close_x = self.close_button.x + (self.close_button.width - close_text.get_width()) // 2
        close_y = self.close_button.y + (self.close_button.height - close_text.get_height()) // 2
        screen.blit(close_text, (close_x, close_y))
        
        # Draw ranked button (blue)
        ranked_color = self.RANKED_HOVER if self.ranked_button.collidepoint(mx, my) else self.RANKED_COLOR
        pygame.draw.rect(screen, ranked_color, self.ranked_button)
        pygame.draw.rect(screen, self.LIGHT, self.ranked_button, 2)
        
        ranked_text = font_medium.render("RANKED", True, self.LIGHT)
        ranked_x = self.ranked_button.x + (self.ranked_button.width - ranked_text.get_width()) // 2
        ranked_y = self.ranked_button.y + (self.ranked_button.height - ranked_text.get_height()) // 2
        screen.blit(ranked_text, (ranked_x, ranked_y))
        
        # Draw lobby button (green)
        lobby_color = self.LOBBY_HOVER if self.lobby_button.collidepoint(mx, my) else self.LOBBY_COLOR
        pygame.draw.rect(screen, lobby_color, self.lobby_button)
        pygame.draw.rect(screen, self.LIGHT, self.lobby_button, 2)
        
        # Two-line text for lobby button
        create_text = font_medium.render("CREATE", True, self.LIGHT)
        lobby_text = font_medium.render("LOBBY", True, self.LIGHT)
        
        create_x = self.lobby_button.x + (self.lobby_button.width - create_text.get_width()) // 2
        lobby_x = self.lobby_button.x + (self.lobby_button.width - lobby_text.get_width()) // 2
        
        screen.blit(create_text, (create_x, self.lobby_button.y + 35))
        screen.blit(lobby_text, (lobby_x, self.lobby_button.y + 65))
    
    def handle_click(self, pos):
        if not self.visible:
            return None
        
        x, y = pos
        
        if self.close_button.collidepoint(x, y):
            self.hide()
            return "close"
        elif self.ranked_button.collidepoint(x, y):
            self.hide()
            if self.on_ranked:
                self.on_ranked()
            return "ranked"
        elif self.lobby_button.collidepoint(x, y):
            self.hide()
            if self.on_lobby:
                self.on_lobby()
            return "lobby"
        
        return None