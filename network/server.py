# This is the network/server.py file.

import socket
import threading
import json
import time
import uuid

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


# --------------------------------------------------
# UDP DISCOVERY SERVER (ANNOUNCEMENT ONLY)
# --------------------------------------------------

class UDPDiscoveryServer:
    def __init__(self, server_ip, game_port, broadcast_port=37020, interval=1):
        self.server_ip = server_ip
        self.game_port = game_port
        self.broadcast_port = broadcast_port
        self.interval = interval

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.running = False
        self.payload = {}

    def update_payload(self, payload: dict):
        """
        Update lobby info to broadcast.
        Password is intentionally NOT included.
        """
        self.payload = payload

    def start(self):
        if self.running:
            return

        self.running = True
        threading.Thread(target=self._run, daemon=True).start()
        print("UDP Discovery Server started")

    def _run(self):
        while self.running:
            if self.payload:
                message = {
                    "type": "Init Lobby",
                    "lobby_name": self.payload.get("lobby_name", "Lobby"),
                    "host_name": self.payload.get("host_name", "Host"),
                    "lobby_password": self.payload.get("password", ""),
                    "ip": self.server_ip,
                    "port": self.game_port
                }

                self.sock.sendto(
                    json.dumps(message).encode(),
                    ("<broadcast>", self.broadcast_port)
                )

            time.sleep(self.interval)

    def stop(self):
        self.running = False
        self.sock.close()

class ServerNetwork:
    def __init__(self, HOST='0.0.0.0', PORT=5555, TRANSPORT_LAYER='TCP'):
        self.ip_address = get_lan_ip()
        print(f"Server running on IP: {self.ip_address}")

        self.HOST = HOST
        self.PORT = PORT
        self.TRANSPORT_LAYER = TRANSPORT_LAYER.strip().upper()

        LAYERS = {
            'TCP': socket.SOCK_STREAM,
            'UDP': socket.SOCK_DGRAM,
        }

        if self.TRANSPORT_LAYER not in LAYERS:
            raise ValueError("Unsupported transport layer.")

        self.server = socket.socket(socket.AF_INET, LAYERS[self.TRANSPORT_LAYER])

        self.clients = {}   # socket -> player_id
        self.players = {}   # player_id -> data
        self.id = 1

        self.running = False

        # ---- Extensions ----
        self.lobby_ext = LobbyServerExtension(self)

        # ---- Discovery ----
        self.discovery_server = UDPDiscoveryServer(
            server_ip=self.ip_address,
            game_port=self.PORT
        )

    def start(self):
        self.running = True
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()
        print(f"Server started on {self.HOST}:{self.PORT} using {self.TRANSPORT_LAYER}")

        self.discovery_server.start()

        while self.running:
            client, addr = self.server.accept()
            print(f"Connection to {client} from {addr} has been established.")

            # Assign ID and initial position
            self.clients[client] = self.id
            self.players[self.id] = [0, 0]  # Initial position

            print(f"Assigned ID {self.id} to client {client}")

            # Send init message to this client
            self.send_to_client(client, {
                'type': 'init',
                'payload': {
                    'player_id': self.id,
                    'players': self.players,
                }
            })

            # Broadcast updated player list to all
            self.broadcast({
                'type': 'update_players',
                'payload': self.players
            })

            self.activate_thread(self.handle_client, client)
            self.id += 1

    def handle_client(self, client):
        buffer = ''
        while self.running:
            try:
                data = client.recv(1024).decode()
                if not data:
                    break
            except ConnectionResetError:
                break

            buffer += data
            while '\n' in buffer:
                try:
                    raw_message, buffer = buffer.split('\n', 1)
                    self.process_message(client, raw_message)
                except Exception as e:
                    print(f"Error processing message: {e}")

        client.close()
        # self.clients.pop(client, None)

    def process_message(self, client, raw_message):
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type')
            payload = message.get('payload')

            request_handler = {
                'lobby_create': self.lobby_ext.handle_create_lobby,
                'get_lobbies': self.lobby_ext.handle_get_lobbies,
                'join_request': self.lobby_ext.handle_join_request,
                'join_decision': self.lobby_ext.handle_join_decision,
            }

            request_func = request_handler.get(msg_type)
            if request_func:
                request_func(client, payload)
            else:
                print(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            print("Received invalid JSON message.")
            return

    def send_to_client(self, client, message: dict):
        try:
            client.sendall((json.dumps(message) + '\n').encode())
        except Exception as e:
            print(f"Error sending to client: {e}")

    def broadcast(self, message: dict):
        for client in list(self.clients.keys()):
            try:
                client.sendall((json.dumps(message) + '\n').encode())
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

    def activate_thread(self, target_func, *args, **kwargs):
        thread = threading.Thread(target=target_func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()


# --------------------------------------------------
# LOBBY SERVER EXTENSION
# --------------------------------------------------

class LobbyServerExtension:
    def __init__(self, server: ServerNetwork):
        self.server = server
        self.lobbies = {}

    def handle_create_lobby(self, client, payload):
        lobby_id = str(uuid.uuid4())

        self.lobbies[lobby_id] = {
            "id": lobby_id,
            "name": payload["lobby_name"],
            "password": payload["lobby_password"],
            "host_client": client,
            "players": {}
        }

        # Update discovery broadcast
        # self.server.discovery_server.update_payload({
        #     "lobby_name": payload["lobby_name"],
        #     "host_name": "Host"
        # })
        host_profile = payload.get("host_profile")

        host_name = "Host"
        if host_profile:
            # Adjust index if your profile structure differs
            host_name = host_profile[1]  # usually username

        self.server.discovery_server.update_payload({
            "lobby_name": payload["lobby_name"],
            "host_name": host_name
        })

        self.server.send_to_client(client, {
            "type": "LOBBY_CREATED",
            "payload": {
                "lobby_id": lobby_id,
                "lobby_name": payload["lobby_name"]
            }
        })

        print(f"Lobby '{payload['lobby_name']}' created")

    def handle_get_lobbies(self, client, payload):
        lobby_list = [
            {
                "id": lobby["id"],
                "name": lobby["name"],
                "players": f"{len(lobby['players'])}/4"
            }
            for lobby in self.lobbies.values()
        ]

        self.server.send_to_client(client, {
            "type": "LOBBY_LIST",
            "payload": lobby_list
        })

    # -------------------------
    # JOIN REQUEST
    # -------------------------
    def handle_join_request(self, client, payload):
        # lobby_id = payload["lobby_id"]
        # player_name = payload["player_name"]

        # lobby = self.lobbies.get(lobby_id)
        # if not lobby:
        #     return

        # request_id = str(uuid.uuid4())

        # lobby["players"][request_id] = {
        #     "client": client,
        #     "name": player_name,
        #     "status": "PENDING"
        # }

        # # Notify host
        # self.server.send_to_client(
        #     lobby["host_client"],
        #     {
        #         "type": "JOIN_REQUEST",
        #         "payload": {
        #             "request_id": request_id,
        #             "player_name": player_name
        #         }
        #     }
        # )
        lobby_id = payload.get("lobby_id")

        # LAN shortcut: assume only one lobby
        if lobby_id is None and self.lobbies:
            lobby = next(iter(self.lobbies.values()))
        else:
            lobby = self.lobbies.get(lobby_id)

        if not lobby:
            return

    # -------------------------
    # HOST DECISION
    # -------------------------
    def handle_join_decision(self, client, payload):
        lobby_id = payload["lobby_id"]
        request_id = payload["request_id"]
        accepted = payload["accepted"]

        lobby = self.lobbies.get(lobby_id)
        if not lobby:
            return

        request = lobby["players"].get(request_id)
        if not request:
            return

        target_client = request["client"]

        if accepted:
            request["status"] = "ACCEPTED"
            response = "ACCEPTED"
        else:
            del lobby["players"][request_id]
            response = "DECLINED"

        self.server.send_to_client(
            target_client,
            {
                "type": "JOIN_RESULT",
                "payload": {"result": response}
            }
        )




if __name__ == "__main__":
    server = ServerNetwork()
    server.start()
