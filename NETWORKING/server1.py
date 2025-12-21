import socket
import threading
import json


class NetworkServer:
    """
    Server-side networking module for a multiplayer game.

    Responsibilities:
    - Accept incoming client connections
    - Receive and decode messages from clients
    - Dispatch messages to appropriate handlers
    - Manage connected client sockets
    """

    def __init__(self, host="0.0.0.0", port=5555, type_of_conn=""):
        """
        Initialize the network server.

        :param host: IP address to bind the server to
        :param port: Port number to listen on
        :param type_of_conn: Connection type ('TCP' or 'UDP')
        """
        self.host = host
        self.port = port
        self.type = type_of_conn.strip().upper()

        # Supported connection types
        types = {
            "TCP": socket.SOCK_STREAM,
            "UDP": socket.SOCK_DGRAM,
        }
        if not (self.type in types.keys()):
            raise ValueError("Type of connection is invalid")
        self.server = socket.socket(socket.AF_INET, types.get(self.type))

        # Provides an easy switch for the system
        self.running = False

        # List of accepted clients
        self.clients = []

    def validation_check(self):
        """
        Perform validation on a newly connected client.

        Intended for future use:
        - Authentication
        - Version checks
        - Rate limiting
        """
        pass

    def handle_broadcast(self, sender, name, message):
        print(f"Broadcast from {name}: {message}")

        msg = {
            "type": "broadcast",
            "payload": {
                "name": name,
                "message": message,
            }
        }
        data = json.dumps(msg) + "\n"

        for client in self.clients:
            if client != sender:
                try:
                    client.sendall(data.encode())
                except Exception as e:
                    print(f"Failed to send message to a client: {e}")

    def process_msg(self, client, msg):
        """
        Validate and process a message received from a client.

        Acts as a central dispatcher for different message types
        (e.g., broadcast, private chat, game state updates).

        :param client: Client socket that sent the message
        :param msg: Parsed JSON message (expected to be a dictionary)
        """
        if not isinstance(msg, dict):
            return

        print("Full message received:", msg)
        msg_type = msg.get("type")
        msg_content = msg.get("payload")

        if not isinstance(msg_type, str):
            print("Message is unreadable. Type should be a string.")
            return

        if msg_content is None:
            print("Message does not contain a payload.")
            return

        scenario_handlers = {
            "broadcast": self.handle_broadcast,
        }

        handler = scenario_handlers.get(msg_type)
        if handler:
            handler(client, **msg_content)

    def handle_client(self, client):
            """
            Handle communication with a single connected client.

            Runs in its own thread. Receives incoming data,
            reconstructs complete JSON messages, and forwards
            them to the message processor.
            """
            # Buffer for partial TCP data
            buffer = ""

            while self.running:
                try:
                    # Receive up to 1024 bytes from the client
                    data = client.recv(1024)
                    if not data:
                        break

                    # Append decoded data to buffer
                    buffer += data.decode()

                    # Process all complete messages in buffer
                    while "\n" in buffer:
                        raw_msg, buffer = buffer.split("\n", 1)

                        try:
                            msg = json.loads(raw_msg)
                            print("Message received successfully:")
                            self.process_msg(client, msg)

                        except json.JSONDecodeError:
                            # Prevent malformed messages from crashing the server
                            print("Invalid JSON:", raw_msg)

                except ConnectionResetError:
                    break

            # Cleanup after client disconnects
            client.close()

            if client in self.clients:
                self.clients.remove(client)

    def activate_thread(self, target_func, *args, daemon=True, **kwargs):
        """
        Create and start a new thread for a given target function.

        :param target_func: Callable to run in a new thread
        :param args: Positional arguments for the target function
        :param daemon: Whether the thread runs as a daemon
        :param kwargs: Keyword arguments for the target function
        :return: The created Thread object
        """
        thread = threading.Thread(
            target=target_func,
            args=args,
            kwargs=kwargs,
        )
        thread.daemon = daemon
        thread.start()
        return thread

    def start(self):
        """
        Start the server and begin accepting client connections.
        """
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.running = True

        print("Server is initialized successfully")

        while self.running:
            client, addr = self.server.accept()
            print("Connected:", addr)

            self.clients.append(client)
            self.activate_thread(self.handle_client, client, daemon=True)

    def shutdown(self):
        """
        Gracefully shut down the server and release resources.
        """
        self.running = False
        self.server.close()


if __name__ == "__main__":
    server = NetworkServer(type_of_conn="TCP")
    server.start()