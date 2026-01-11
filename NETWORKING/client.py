import socket
import threading
import json
import time

def get_lan_ip():
    '''
    Helper for getting the ip of each machine
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


class UDPDiscoveryClient:
    def __init__(self, listening_port=37020):
        self.listen_port = listening_port

        self.UDPClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDPClient.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.UDPClient.bind(("", self.listen_port))

        self.servers_detected = {}
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        print("Detecting available servers...")

        while self.running:
            try:
                data, addr = self.UDPClient.recvfrom(1024)
                msg = json.loads(data.decode())

                if msg.get('type') == 'Init Lobby':
                    server_id = (msg['ip'], msg['port'])
                    self.servers_detected[server_id] = msg
            except Exception as e:
                pass

    def get_servers(self):
        return list(self.servers_detected.values())
    
    def shutdown(self):
        self.running = False
        self.UDPClient.close()
        

class ClientNetwork:
    def __init__(self, HOST=None, PORT=5555, TRANSPORT_LAYER='TCP', role='client'):
        self.HOST = HOST
        self.PORT = PORT
        self.TRANSPORT_LAYER = TRANSPORT_LAYER.strip().upper()
        self.role = role
        self.ip = get_lan_ip()
        print(f"Client running on IP: {self.ip}")

        LAYERS = {
            'TCP': socket.SOCK_STREAM,
            'UDP': socket.SOCK_DGRAM,
        }

        if self.TRANSPORT_LAYER not in LAYERS:
            raise ValueError("Unsupported transport layer. Use 'TCP' or 'UDP'.")
        self.client = socket.socket(socket.AF_INET, LAYERS[self.TRANSPORT_LAYER])

        self.players = {}   # player_id -> position

        self.my_id = None
        self.connected = False

    def get_players(self):
        return self.players

    def start(self):
        discovery = UDPDiscoveryClient()
        discovery.start()

        # Give time for UDP broadcasts
        time.sleep(2)

        servers = discovery.get_servers()
        print("Discovered LAN servers:", servers)

        if not servers:
            print("No LAN servers found.")
            return

        # CLIENT: connect to the first discovered server
        if self.role == "client":
            server = servers[0]
            self.connect(server["ip"], server["port"])
            return

        # HOST: connect only to its own LAN server (Minecraft behavior)
        if self.role == "host":
            lan_ip = self.ip

            for server in servers:
                if server["ip"] == lan_ip:
                    self.connect(server["ip"], server["port"])
                    return

            print("Host LAN server not found in discovery list.")


    # def start(self):
    #     if self.role == 'client':
    #         discovery = UDPDiscoveryClient()
    #         discovery.start()

    #         time.sleep(2)  # allow discovery

    #         servers = discovery.get_servers()
    #         print("Discovered servers:", servers)

    #         if servers:
    #             server = servers[0]
    #             self.connect(server["ip"], server["port"])
    #     else:
    #         self.connect(self.ip, self.PORT)

    def connect(self, host, port):
        self.HOST = host
        self.PORT = port

        self.client.connect((self.HOST, self.PORT))
        self.connected = True

        print(f"Connected to server {self.HOST}:{self.PORT}")

        self.activate_thread(self.receive, daemon=False)

    def send(self, message: dict):
        if self.connected:
            if 'type' not in message:
                raise ValueError("Message must contain a 'type' key.")
            if 'payload' not in message:
                raise ValueError("Message must contain a 'payload' key.")

            self.client.sendall((json.dumps(message) + '\n').encode())

    def message_packager(self, msg_type: str, payload: dict) -> dict:
        return {
            'type': msg_type,
            'payload': payload
        }

    def activate_thread(self, target_func, *args, daemon=True, **kwargs):
        thread = threading.Thread(target=target_func, args=args, kwargs=kwargs)
        thread.daemon = daemon
        thread.start()

    def receive(self):
        buffer = ''
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break

                buffer += data
                while '\n' in buffer:
                    try:
                        raw_message, buffer = buffer.split('\n', 1)
                        self.process_message(raw_message)
                    except Exception as e:
                        print(f"Error processing message: {e}")

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
                player_id = payload['player_id']
                position = payload['position']
                self.players[player_id] = position
                print(f"Player {player_id} moved to {position}")

            else:
                print(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            print("Invalid JSON received")

if __name__ == "__main__":
    client_module = ClientNetwork(role='client')
    client_module.start()