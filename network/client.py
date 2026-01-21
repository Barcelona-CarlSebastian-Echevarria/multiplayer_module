# this is the network/client.py file

import socket
import threading
import json
import time


# -----------------------------
# Helpers
# -----------------------------
def get_lan_ip():
    """Return this machine's LAN IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


# -----------------------------
# UDP DISCOVERY CLIENT (LAN PASSIVE)
# -----------------------------
class UDPDiscoveryClient:
    def __init__(self, listening_port=37020):
        self.listen_port = listening_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.listen_port))

        self.lobbies = {}  # key = (ip, port)
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._receive_loop, daemon=True).start()
        print("UDP Discovery Client started")

    def _receive_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                msg = json.loads(data.decode())
                if msg.get("type") == "Init Lobby":
                    lobby_key = (msg["ip"], msg["port"])
                    self.lobbies[lobby_key] = msg
            except Exception:
                continue

    def get_lobbies(self):
        """Return a list of discovered lobby info."""
        return list(self.lobbies.values())

    def stop(self):
        self.running = False
        self.sock.close()


# -----------------------------
# CLIENT NETWORK (TCP)
# -----------------------------
class ClientNetwork:
    def __init__(self, HOST=None, PORT=5555, TRANSPORT_LAYER='TCP', role='client'):
        self.HOST = HOST
        self.PORT = PORT
        self.TRANSPORT_LAYER = TRANSPORT_LAYER.strip().upper()
        self.role = role
        self.ip = get_lan_ip()
        print(f"Client running on IP: {self.ip}, role: {self.role}")

        LAYERS = {'TCP': socket.SOCK_STREAM, 'UDP': socket.SOCK_DGRAM}
        if self.TRANSPORT_LAYER not in LAYERS:
            raise ValueError("Unsupported transport layer. Use 'TCP' or 'UDP'.")

        self.client = socket.socket(socket.AF_INET, LAYERS[self.TRANSPORT_LAYER])
        self.connected = False
        self.players = {}
        self.my_id = None

        # Optional extension for lobby commands
        self.ext = None

    # -----------------------------
    # Start Discovery (non-blocking)
    # -----------------------------
    def start_discovery(self):
        """Start UDP discovery to populate available LAN lobbies. Non-blocking."""
        self.discovery = UDPDiscoveryClient()
        self.discovery.start()
        # Give a moment for initial broadcasts, but do not auto-connect
        threading.Thread(target=self._discovery_wait, daemon=True).start()

    def _discovery_wait(self, wait_time=2):
        time.sleep(wait_time)
        print(f"Discovered LAN lobbies: {self.discovery.get_lobbies()}")

    # -----------------------------
    # Manual Connect (UI-driven)
    # -----------------------------
    def connect(self, host, port):
        """Connect to the selected server manually (UI decides host)."""
        if self.connected:
            return

        self.HOST = host
        self.PORT = port
        self.client.connect((host, port))
        self.connected = True
        print(f"Connected to server {host}:{port}")

        # Start receiving messages in a separate thread
        self.activate_thread(self._receive_loop, daemon=True)

    def disconnect(self):
        if self.connected:
            self.client.close()
            self.connected = False

    # -----------------------------
    # Send/Receive
    # -----------------------------
    def send(self, message: dict):
        if self.connected:
            if 'type' not in message or 'payload' not in message:
                raise ValueError("Message must contain 'type' and 'payload'.")
            self.client.sendall((json.dumps(message) + '\n').encode())

    def message_packager(self, msg_type: str, payload: dict) -> dict:
        return {'type': msg_type, 'payload': payload}

    def _receive_loop(self):
        buffer = ""
        while self.connected:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    raw_message, buffer = buffer.split('\n', 1)
                    self.process_message(raw_message)
            except ConnectionResetError:
                break

    def process_message(self, raw_message):
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type')
            payload = message.get('payload')

            if msg_type == 'init':
                self.my_id = payload['player_id']
                self.players = payload['players']
                print(f"My ID: {self.my_id}, Current players: {self.players}")

            elif msg_type == 'update_players':
                self.players = payload
                print(f"Updated players list: {self.players}")

            elif msg_type == 'update_position':
                self.players[payload['player_id']] = payload['position']

            elif msg_type == 'LOBBY_CREATED':
                print(f"Lobby created: {payload}")

            else:
                print(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            print("Invalid JSON received")

    # -----------------------------
    # Threading helper
    # -----------------------------
    def activate_thread(self, target_func, *args, daemon=True, **kwargs):
        t = threading.Thread(target=target_func, args=args, kwargs=kwargs)
        t.daemon = daemon
        t.start()


# -----------------------------
# CLIENT LOBBY EXTENSION
# -----------------------------
class LobbyClientExtension:
    def __init__(self, client_network):
        self.client = client_network

    def send_get_lobbies(self):
        msg = self.client.message_packager('get_lobbies', {})
        self.client.send(msg)

    def send_create_lobby(self, profile, lobby_data):
        payload = {
            'lobby_name': lobby_data['lobby_name'],
            'lobby_password': lobby_data['passcode'],
            'host_profile': profile
        }
        msg = self.client.message_packager('lobby_create', payload)
        self.client.send(msg)
        print("Create lobby request sent.")

    def send_join_request(self, lobby_id, player_name):
            msg = self.client.message_packager(
                "join_request",
                {
                    "lobby_id": lobby_id,
                    "player_name": player_name
                }
            )
            self.client.send(msg)

    def send_join_decision(self, lobby_id, request_id, accepted):
        msg = self.client.message_packager(
            "join_decision",
            {
                "lobby_id": lobby_id,
                "request_id": request_id,
                "accepted": accepted
            }
        )
        self.client.send(msg)
