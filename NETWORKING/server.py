import socket
import threading
import json
import time

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

class UDPDiscoveryServer:
    def __init__(self, server_ip, game_port, broadcast_port=37020, interval=1):
        self.server_ip = server_ip
        self.game_port = game_port
        self.broadcast_port = broadcast_port
        self.interval = interval

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.running = False

    def start(self):
        self.running = True
        print("UDP Discovery Server started")

        while self.running:
            message = {
                "type": "Init Lobby",
                "name": "# Insert player name here",
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
            raise ValueError("Unsupported transport layer. Use 'TCP' or 'UDP'.")
        self.server = socket.socket(socket.AF_INET, LAYERS[self.TRANSPORT_LAYER])
        self.clients = {}   # socket -> player_id
        self.players = {}   # player_id -> position
        self.id = 1
        self.discovery_server = UDPDiscoveryServer(
            server_ip = self.ip_address,
            game_port=self.PORT
        )
        self.running = False

    def start(self):
        self.running = True
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()
        print(f"Server started on {self.HOST}:{self.PORT} using {self.TRANSPORT_LAYER}")

        threading.Thread(target=self.discovery_server.start,daemon=True).start()

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

    def process_message(self, client, raw_message):
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type')
            payload = message.get('payload')

            request_handler = {
                'move': self.handle_move,
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

    # Should be in game state
    # def handle_move(self, client, payload):
        # player_id = self.clients[client]
        # new_position = payload.get('direction')

        # if new_position == 'left':
        #     self.players[player_id][0] -= PLAYER['speed']

        # if new_position == 'right':
        #     self.players[player_id][0] += PLAYER['speed']

        # if new_position == 'up':
        #     self.players[player_id][1] -= PLAYER['speed']

        # if new_position == 'down':
        #     self.players[player_id][1] += PLAYER['speed']

        # if player_id in self.players:
        #     print(f"Player {player_id} moved to {self.players[player_id]}")
        # else:
        #     print(f"Player ID {player_id} not found.")
        
        # Broadcast updated position
        # self.broadcast({
        #     'type': 'update_position',
        #     'payload': {
        #         'player_id': player_id,
        #         'position': self.players[player_id]
        #     }
        # })


if __name__ == "__main__":
    server = ServerNetwork()
    server.start()
