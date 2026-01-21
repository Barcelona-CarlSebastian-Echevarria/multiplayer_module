# This is the multiplayer_create_lobby.py file.

import pygame
import os
import sys
import pygame_gui
import threading
import time

# Get the current directory 
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
parent_dir = os.path.dirname(current_dir)
# Add parent directory to Python path
sys.path.insert(0, parent_dir)

# Additional components
from game_pages.create_host_popup import CreateLobbyPopup
from database_db.profile_manage import ProfileManager
from network.server import UDPDiscoveryServer,ServerNetwork, LobbyServerExtension
from network.client import ClientNetwork, LobbyClientExtension
from game_pages.create_join_popup import JoinLobbyPopup
from game_pages.create_wait_popup import WaitingPopup


class LobbyUI:
    """
    UI-ONLY LOBBY MODULE

    Standalone-safe:
    - Renders without networking
    - Displays empty states
    - No callbacks required to function
    """

    def __init__(self):
        # pygame.init()

        # ---------- CONFIG ----------
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.MAX_PLAYERS = 2

        # self.screen = pygame.display.set_mode(
        #     (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        # )
        # pygame.display.set_caption("Multiplayer Lobby")
        # self.clock = pygame.time.Clock()

        self.ui_manager = pygame_gui.UIManager(
            (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )

        ASSETS_DIR = os.path.join(
            parent_dir,
            "subnautic_shooter",
            "assets",
            "images",
            "pages"
        )
        self.background = pygame.image.load(os.path.join(ASSETS_DIR, "background_final.png")).convert()
        self.background = pygame.transform.scale(self.background, (self.SCREEN_WIDTH, self.SCREEN_HEIGHT))

        # ---------- STATE ----------
        self.players = []          # empty by default
        self.join_lobbies = []     # empty by default
        self.last_lobbies_count = 0
        self.current_mode = "JOIN" # default visible state

        self.main_panel_elements = {}

        # ---------- NETWORK HOOKS (OPTIONAL) ----------
        self.send_get_lobbies = None
        self.send_create_lobby = None
        self.send_join_lobby = None
        self.send_accept_player = None
        self.send_decline_player = None

        # ---------- BUILD ----------
        self._build_ui()
        self._render_empty_state()  # ⭐ IMPORTANT

        # ---------- POPUPS ----------
        self.create_popup = CreateLobbyPopup(
            ui_manager=self.ui_manager,
            screen_size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            on_confirm=self._on_create_confirm,
            on_cancel=self._on_create_cancel
        )

        self.join_popup = JoinLobbyPopup(
            ui_manager=self.ui_manager,
            screen_size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            on_confirm=self._on_join_confirm,
            on_cancel=self._on_join_cancel
        )

        self.waiting_popup = WaitingPopup(
            ui_manager=self.ui_manager,
            screen_size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        )

        # ---------- POPUPS ----------
        self.selected_lobby = None

        # ---------- PROFILE MANAGEMENT ----------
        self.profile_manager = ProfileManager()
        self.profile = self.profile_manager.load_profile()
        if self.profile:
            print("Loaded profile:", self.profile[1])

        else:
            self.profile = None

        # ---------- JOIN REQUESTS ----------
        self.join_request_elements = {}


    # ==================================================
    # ================= MAIN LOOP =======================
    # ==================================================
    def update(self, events, dt=0):

        for event in events:
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         running = False
            #         if hasattr(self, 'discovery_running'):
            #             self.discovery_running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("ESC pressed - returning to main menu")
                    running = False
                    if hasattr(self, 'discovery_running'):
                        self.discovery_running = False
                    return ("POP", None)
            
            if event.type == pygame_gui.UI_BUTTON_PRESSED:

                # Toggle JOIN / CREATE
                if event.ui_element == self.mode_button:
                    if self.current_mode == "JOIN":
                        self.current_mode = "CREATE"
                        self.mode_button.set_text("CREATE")

                        # Show password row
                        self.password_label.show()
                        self.info_labels["password"].show()

                    else:
                        self.current_mode = "JOIN"
                        self.mode_button.set_text("JOIN")
                        # Hide password row
                        self.password_label.hide()
                        self.info_labels["password"].hide()

                # Play button action
                elif event.ui_element == self.play_button:
                    print(f"PLAY pressed in {self.current_mode} mode")

                    if self.current_mode == "JOIN":
                        self.start_lan_discovery()

                    elif self.current_mode == "CREATE":
                        self.info_labels["lobby_name"].set_text(
                            "New Lobby (Local)"
                        )
                        self.create_popup.show()

                # Handle JOIN button clicks for discovered lobbies
                for item in self.main_panel_elements.values():
                    if isinstance(item, dict) and event.ui_element == item.get("join_button"):
                        self.selected_lobby = item["data"]
                        self.join_popup.show()

                # Handle accept/decline buttons for join requests
                for req_id, item in self.join_request_elements.items():
                    if event.ui_element == item["accept"]:
                        self.client_network.ext.send_join_decision(
                            self.current_lobby_id,
                            req_id,
                            True
                        )

                    elif event.ui_element == item["decline"]:
                        self.client_network.ext.send_join_decision(
                            self.current_lobby_id,
                            req_id,
                            False
                        )

            # Process UI events
            self.create_popup.process_event(event)
            self.join_popup.process_event(event)
            self.ui_manager.process_events(event)
        # Update UI manager
        self.ui_manager.update(dt)

        if self.current_mode == "JOIN":
            if len(self.join_lobbies) != self.last_lobbies_count:
                self._render_join_lobbies()
                self.last_lobbies_count = len(self.join_lobbies)

        return None
    
    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        self.ui_manager.draw_ui(screen)

    # ==================================================
    # ==========  Join Requests =======================
    # ==================================================

    def _clear_join_requests(self):
        for item in self.join_request_elements.values():
            item["accept"].kill()
            item["decline"].kill()
        self.join_request_elements.clear()

    def render_join_requests(self, requests):
        self._clear_main_panel()
        self._clear_join_requests()

        y = 10
        for req in requests:
            panel = pygame_gui.elements.UIPanel(
                pygame.Rect(20, y, 1100, 70),
                manager=self.ui_manager,
                container=self.scroll
            )

            # Player name
            pygame_gui.elements.UILabel(
                pygame.Rect(20, 20, 300, 30),
                text=req["player_name"],
                manager=self.ui_manager,
                container=panel
            )

            # ACCEPT (circle feel)
            accept_btn = pygame_gui.elements.UIButton(
                pygame.Rect(950, 15, 40, 40),
                text="✓",
                manager=self.ui_manager,
                container=panel
            )

            # DECLINE (circle feel)
            decline_btn = pygame_gui.elements.UIButton(
                pygame.Rect(1000, 15, 40, 40),
                text="✕",
                manager=self.ui_manager,
                container=panel
            )

            self.join_request_elements[req["request_id"]] = {
                "accept": accept_btn,
                "decline": decline_btn,
                "data": req
            }

            y += 85

    # ==================================================
    # ========== CREATE: JOIN_POPUP CALLBACKS =======================
    # ==================================================
    def _on_join_confirm(self, passcode):
        print("\n[UI] Join confirmed")
        print("[UI] Selected lobby:", self.selected_lobby)

        host_ip = self.selected_lobby["ip"]
        host_port = self.selected_lobby["port"]

        print(f"[UI] Connecting to host {host_ip}:{host_port}")
        self.client_network.connect(host_ip, host_port)

        player_name = self.profile[1] if self.profile else "Guest"

        print("[UI] Sending join request as:", player_name)
        self.client_network.ext.send_join_request(
            lobby_id=None,
            player_name=player_name
        )

        print("[UI] Waiting for host decision...")
        self.waiting_popup.show()


    def _on_join_cancel(self):
        print("Join cancelled")
        self.selected_lobby = None

    # ==================================================
    # ========== CREATE: HOST_POPUP CALLBACKS =======================
    # ==================================================
    def _on_create_confirm(self, lobby_name, passcode):
        """
        Called when user confirms lobby creation.
        UI-only responsibility:
        - Close popup
        - Update UI state
        - Forward data via network hook (if connected)
        """
        print("Create confirmed:", lobby_name, passcode)

        self.current_mode = "CREATE"
        self.info_labels["lobby_name"].set_text(lobby_name)
        self.info_labels["password"].set_text(passcode)
        # Ensure password is visible
        self.password_label.show()
        self.info_labels["password"].show()

        self.server_network = ServerNetwork()
        # Start server in background thread so UI doesn't freeze
        threading.Thread(target=self.server_network.start, daemon=True).start()
        # Setup lobby extension (handles lobby commands)
        self.server_network.lobby_ext = LobbyServerExtension(self.server_network)

        # Start Client as Host
        self.client_network = ClientNetwork(role="host")
        self.client_network.ext = LobbyClientExtension(self.client_network)
        # Directly connect to own server
        self.client_network.connect(self.server_network.ip_address, self.server_network.PORT)

        if self.client_network.ext.send_create_lobby:
            self.client_network.ext.send_create_lobby(
                self.profile,
                {"lobby_name": lobby_name, "passcode": passcode}
            )

    def _on_create_cancel(self):
        """
        Called when user cancels lobby creation.
        """
        print("Create cancelled")

    # ==================================================
    # ================= JOIN Mode ========================
    # ==================================================   
    def start_lan_discovery(self):
        """
        Start background LAN discovery for available lobbies.
        Populates self.join_lobbies.
        """
        # Initialize client network for JOIN
        self.client_network = ClientNetwork(role="client")
        self.client_network.ext = LobbyClientExtension(self.client_network)

        # Start UDP discovery in background
        self.client_network.start_discovery()

        # Start a thread to periodically update the local join_lobbies list
        def update_lobbies():
            self.discovery_running = True
            while self.discovery_running:
                # Fetch discovered lobbies from the discovery client
                if hasattr(self.client_network, 'discovery'):
                    self.join_lobbies = self.client_network.discovery.get_lobbies()
                # Sleep a short time to avoid hogging CPU
                time.sleep(1)
            self.discovery_running = False

        threading.Thread(target=update_lobbies, daemon=True).start()

    def _render_join_lobbies(self):
        """
        Render all discovered lobbies in the main panel.
        Each lobby gets a rectangular container with:
        - Lobby name
        - Host name
        - Join button
        """
        # Clear previous elements
        self._clear_main_panel()

        if not self.join_lobbies:
            # Show empty state if no lobbies
            self._render_empty_state()
            return

        y_offset = 10  # initial vertical position

        for idx, lobby in enumerate(self.join_lobbies):
            # Container for each lobby
            lobby_panel = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect(10, y_offset, 1140, 80),
                manager=self.ui_manager,
                container=self.scroll,
            )

            # Lobby name
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 10, 300, 25),
                text=f"Lobby: {lobby.get('lobby_name', 'Unknown')}",
                manager=self.ui_manager,
                container=lobby_panel
            )

            # Host name
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(10, 40, 300, 25),
                text=f"Host: {lobby.get('host_name', 'Unknown')}",
                manager=self.ui_manager,
                container=lobby_panel
            )

            # Join button
            join_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(1050, 20, 80, 40),
                text="JOIN",
                manager=self.ui_manager,
                container=lobby_panel
            )

            # Save reference so we can handle events later
            self.main_panel_elements[f"lobby_{idx}"] = {
                "panel": lobby_panel,
                "join_button": join_button,
                "data": lobby
            }

            y_offset += 90  # spacing between lobby panels

    # ==================================================
    # ================= UI BUILD ========================
    # ==================================================
    def _build_ui(self):
        self.info_labels = {}

        # Top labels
        self.info_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(50, 15, 380, 115),
            manager=self.ui_manager
        )

        # Labels inside info panel
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, 100, 25),
            text="Lobby Name:",
            manager=self.ui_manager,
            container=self.info_panel
        )

        self.info_labels["lobby_name"] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 10, 240, 25),
            text="",
            manager=self.ui_manager,
            container=self.info_panel
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(-6, 70, 100, 25),
            text="Players:",
            manager=self.ui_manager,
            container=self.info_panel
        )

        self.info_labels["player_count"] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(40, 70, 100, 25),
            text= f"{len(self.players) + 1} / 2",
            manager=self.ui_manager,
            container=self.info_panel
        )

        # --Mode Buttons---
        self.mode_button_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(900, 20, 260, 50),
            manager=self.ui_manager
        )

        # Main text button (JOIN / CREATE)
        self.mode_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(0, 0, 200, 50),
            text="JOIN",
            manager=self.ui_manager,
            container=self.mode_button_panel
        )

        # Play button (▶)
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(205, 0, 55, 50),
            text=">>",
            manager=self.ui_manager,
            container=self.mode_button_panel
        )

        # Password label (hidden by default)
        self.password_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 40, 100, 25),
            text="Password:",
            manager=self.ui_manager,
            container=self.info_panel,
            visible=False
        )

        self.info_labels["password"] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(120, 40, 240, 25),
            text="",
            manager=self.ui_manager,
            container=self.info_panel,
            visible=False
        )

        # Main panel with scrolling area
        self.main_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(50, 150, 1180, 420),
            manager=self.ui_manager
        )

        self.scroll = pygame_gui.elements.UIScrollingContainer(
            relative_rect=pygame.Rect(10, 10, 1160, 400),
            manager=self.ui_manager,
            container=self.main_panel
        )

    # ==================================================
    # =============== EMPTY STATE =======================
    # ==================================================
    def _render_empty_state(self):
        self._clear_main_panel()

        # Add the label to the scroll container
        no_lobbies_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(400, 160, 400, 40),
            text="No lobbies available",
            manager=self.ui_manager,
            container=self.scroll
        )
        self.main_panel_elements["no_lobbies_label"] = no_lobbies_label

    # ==================================================
    # =============== UI HELPERS ========================
    # ==================================================
    def _clear_main_panel(self):
        # Remove all elements from the scroll container
        for key in list(self.main_panel_elements.keys()):
            element = self.main_panel_elements[key]
            element.kill()
            del self.main_panel_elements[key]

    def _update_player_count(self):
        count = len([p for p in self.players if p.get("status") == "ACCEPTED"])
        self.info_labels["player_count"].set_text(
            f"{count} / {self.MAX_PLAYERS}"
        )
