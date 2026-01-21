# This is the start menu page

import pygame
import os
import sys
import pygame_gui

# Get the current directory 
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
parent_dir = os.path.dirname(current_dir)
# Add parent directory to Python path
sys.path.insert(0, parent_dir)

# Import modules
from database_db.profile_manage import ProfileManager
from game_pages.start_multiplayer_popup import MultiplayerPopup
from game_pages.start_profile_popup import StartProfilePopup
from game_pages.multiplayer_create_lobby import LobbyUI
from subnautic_shooter.game.game import Game
from game_pages.start_profile_widget import ProfileWidget

class StartMenu:
    def __init__(self):
        pygame.init()
        
        self.WIDTH, self.HEIGHT = 1280, 720
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Start Menu")
        
        # Load background
        ASSETS_DIR = os.path.join(
            parent_dir,
            "subnautic_shooter",
            "assets",
            "images",
            "pages"
        )
        self.bg_image = pygame.image.load(os.path.join(ASSETS_DIR, "background_final.png")).convert()
        self.bg_image = pygame.transform.scale(self.bg_image, (self.WIDTH, self.HEIGHT))
        
        self.clock = pygame.time.Clock()
        
        # Load fonts
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        FONT_PATH = os.path.join(BASE_DIR, "PressStart2P-Regular.ttf")
        
        self.title_font = pygame.font.Font(FONT_PATH, 48)
        self.menu_font = pygame.font.Font(FONT_PATH, 24)
        self.popup_title_font = pygame.font.Font(FONT_PATH, 32)
        self.popup_button_font = pygame.font.Font(FONT_PATH, 28)
        self.popup_desc_font = pygame.font.Font(FONT_PATH, 16)
        
        # Colors
        self.LIGHT = (200, 200, 200)
        self.DARK = (0, 0, 0)
        self.SHADOW = (0, 0, 0)
        
        # Menu options
        self.options = ["Singleplayer", "Multiplayer", "Options", "Quit"]
        self.selected = 0
        self.menu_rects = []

        # ---------------- PROFILE SYSTEM  ----------------
        self.profile_manager = ProfileManager()
        self.profile = None  # cached loaded profile
        # --------------------------------------------------------

        # Pygame GUI Manager
        self.ui_manager = pygame_gui.UIManager((self.WIDTH, self.HEIGHT))
    
        # Profile Widget (top corner UI)
        self.profile_widget = ProfileWidget(self.ui_manager, self.WIDTH)

        # Load profile if exists
        self.profile = self.profile_manager.load_profile()
        self.profile_widget.set_profile(self.profile)

         # Create popup
        self.popup = MultiplayerPopup(
            self.WIDTH, 
            self.HEIGHT,
            on_ranked=self.on_ranked_selected,
            on_lobby=self.on_lobby_selected
        )
        # Popup setups
        self.profile_popup = StartProfilePopup(
            ui_manager=self.ui_manager,
            screen_size=(self.WIDTH, self.HEIGHT),
            on_confirm=self.on_profile_confirm,
            on_cancel=self.on_profile_cancel
        )
        
        self.running = True
    
    def draw_text(self, text, font, x, y, color=None):
        if color is None:
            color = self.LIGHT
            
        shadow = font.render(text, True, self.SHADOW)
        self.screen.blit(shadow, (x + 6, y + 6))
        
        for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
            outline = font.render(text, True, self.DARK)
            self.screen.blit(outline, (x + dx, y + dy))
        
        main = font.render(text, True, color)
        self.screen.blit(main, (x, y))
    
    def draw_menu(self):
        self.screen.blit(self.bg_image, (0, 0))
        
        title_text = "SUBNAUTIC SHOOTER"
        title_surface = self.title_font.render(title_text, True, self.LIGHT)
        title_x = self.WIDTH // 2 - title_surface.get_width() // 2
        self.draw_text(title_text, self.title_font, title_x, 160)
        
        self.menu_rects = []
        
        for i, option in enumerate(self.options):
            y = 270 + i * 65
            text_surface = self.menu_font.render(option, True, self.LIGHT)
            rect = text_surface.get_rect(center=(self.WIDTH // 2, y))
            self.menu_rects.append(rect)
            
            self.draw_text(option, self.menu_font, rect.x, rect.y)
            
            if i == self.selected:
                self.draw_text(">", self.menu_font, rect.left - 50, rect.y)

        self.profile_widget.draw(self.screen)
    
    def update_mouse_hover(self):
        if self.popup.visible:
            return
            
        mx, my = pygame.mouse.get_pos()
        self.profile_widget.update_hover((mx, my))
        for i, rect in enumerate(self.menu_rects):
            if rect.collidepoint(mx, my):
                self.selected = i

    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000
            
            for event in pygame.event.get():
                self.ui_manager.process_events(event)
                self.profile_popup.process_event(event)

                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.popup.visible:
                            result = self.popup.handle_click(event.pos)
                            if result == "ranked":
                                print("RANKED button clicked")
                            elif result == "lobby":
                                print("CREATE LOBBY button clicked")
                                self.launch_lobby()
                        else:
                            self.handle_menu_click(event.pos)
                
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
            
            self.update_mouse_hover()
            self.draw_menu()
            self.popup.draw(
                self.screen,
                self.popup_desc_font,
                self.popup_button_font,
                self.popup_title_font
            )
            
            self.ui_manager.update(time_delta)
            self.ui_manager.draw_ui(self.screen)
            pygame.display.update()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    # ==================================================
    # ========== Profile: POPUP CALLBACKS =======================
    # ==================================================

    def on_profile_confirm(self, name):
        self.profile_manager.create_profile(name)
        self.profile = self.profile_manager.load_profile()
        self.profile_widget.set_profile(self.profile)
        print(f"[PROFILE CREATED] Logged in as {self.profile[1]}")


    def on_profile_cancel(self):
        self.profile_popup.reset()
        print("Profile creation cancelled")

    # ==================================================
    # ========== Multiplayer Lobby for transitioning =======================
    # ==================================================
    def launch_lobby(self):
        """
        Transfers control from StartMenu to LobbyUI
        """
        self.running = False  # stop menu loop
        pygame.quit()  # Clean up pygame
        
        try:
            from multiplayer_create_lobby import LobbyUI
            lobby = LobbyUI()
            lobby.run()
        except ImportError as e:
            print(f"Error: Could not import LobbyUI - {e}")
        except Exception as e:
            print(f"Error running lobby: {e}")
        
        # Exit game when lobby closes
        sys.exit()

    # ---------------- DB Functions ----------------
    def validate_profile(self):
        """
        Returns True if a profile exists.
        Returns False if no profile exists.
        """
        self.profile = self.profile_manager.load_profile()

        if self.profile:
            print(f"[PROFILE LOADED] Current player: {self.profile[1]}")
            return True

        print("[PROFILE] No profile found")
        return False

    # ------------------------------------------------------------

    # def handle_menu_click(self, pos):
        # if self.popup.visible:
        #     return

        # x, y = pos
        # for i, rect in enumerate(self.menu_rects):
        #     if rect.collidepoint(x, y):
        #         option = self.options[i]
        #         self.handle_menu_action(option)
    
    def handle_menu_click(self, pos):
        if self.popup.visible:
            return None
        
        # Profile widget click
        clicked = self.profile_widget.handle_click(
            pos,
            on_no_profile=self.profile_popup.show,
            on_show_stats=self.profile_widget.show_stats_popup
        )
        if clicked:
            return None

        x, y = pos
        for i, rect in enumerate(self.menu_rects):
            if rect.collidepoint(x, y):
                option = self.options[i]
                return self.handle_menu_action(option)
        return None

    # def handle_keydown(self, event):
    #     if self.popup.visible:
    #         return
    #     elif event.key == pygame.K_UP:
    #         self.selected = (self.selected - 1) % len(self.options)

    #     elif event.key == pygame.K_DOWN:
    #         self.selected = (self.selected + 1) % len(self.options)

    #     elif event.key == pygame.K_RETURN:
    #         option = self.options[self.selected]
    #         self.handle_menu_action(option)

    def handle_keydown(self, event):
        if self.popup.visible:
            return None

        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self.options)

        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self.options)

        elif event.key == pygame.K_RETURN:
            option = self.options[self.selected]
            return self.handle_menu_action(option)

        elif event.key == pygame.K_ESCAPE:
            return ("QUIT", None)

        return None


    # def handle_menu_action(self, option):

    #     if option == "Singleplayer":
    #         if not self.validate_profile():
    #             self.profile_popup.show()
    #             return None

    #         print("Starting Singleplayer Game...")
    #         from subnautic_shooter.game.game import Game
    #         return ("PUSH", Game())

    #     elif option == "Multiplayer":
    #         if not self.validate_profile():
    #             self.profile_popup.show()
    #             return None

    #         print("Opening Multiplayer Popup...")
    #         self.popup.show()
    #         return None
        
    #     elif option == "Options":
    #         print("Options selected - not implemented yet")
    #         return None

    #     elif option == "Quit":
    #         return ("QUIT", None)

    def handle_menu_action(self, option):
        if option == "Singleplayer":
            if not self.validate_profile():
                self.profile_popup.show()
                return None
            from subnautic_shooter.game.game import Game
            return ("PUSH", Game())

        if option == "Multiplayer":
            if not self.validate_profile():
                self.profile_popup.show()
                return None
            self.popup.show()
            return None

        elif option == "Quit":
            return ("QUIT", None)

        return None

    
    def on_ranked_selected(self):
        """Called when RANKED button is clicked"""
        print("Ranked mode selected")
        # TODO: Implement ranked matchmaking
    
    def on_lobby_selected(self):
        """Called when CREATE LOBBY button is clicked"""
        return ("PUSH", LobbyUI())
    
    def update(self, events, dt=0):
        for event in events:
            self.ui_manager.process_events(event)
            self.profile_popup.process_event(event)

            if event.type == pygame.QUIT:
                return ("QUIT", None)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.popup.visible:
                    result = self.popup.handle_click(event.pos)
                    if result == "lobby":
                        return ("PUSH", LobbyUI())
                else:
                    result = self.handle_menu_click(event.pos)
                    if result:
                        return result

            elif event.type == pygame.KEYDOWN:
                result = self.handle_keydown(event)
                if result:
                    return result

        self.update_mouse_hover()
        return None
    
    def draw(self, screen):
        self.draw_menu()

        self.popup.draw(
            self.screen,
            self.popup_desc_font,
            self.popup_button_font,
            self.popup_title_font
        )

        self.ui_manager.update(0)
        self.ui_manager.draw_ui(screen)


if __name__ == "__main__":
    menu = StartMenu()
    menu.run()