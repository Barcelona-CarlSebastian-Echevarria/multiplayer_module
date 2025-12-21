import socket
import threading
import json


class ClientNetwork:
    """
    Client-side networking module for a multiplayer game.

    Responsibilities:
    - Establish a TCP connection to the game server
    - Send structured JSON messages to the server
    - Receive and process messages asynchronously
    """

    def __init__(self, name, host="127.0.0.1", port=5555):
        """
        Initialize the client network.

        :param name: Display name or identifier for the client
        :param host: Server IP address to connect to
        :param port: Server port number
        """
        self.name = name
        self.host = host
        self.port = port

        # Create a TCP socket for communication with the server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Message routing mode (e.g., broadcast, private, game)
        self.mode = "broadcast"

    def handle_broadcast(self, name, message):
        print(f"\nBroadcast from {name}: {message}")

    def process_msg(self, msg):
        """
        Validate and process a message received from the server.

        This function is a placeholder for future message dispatch logic
        (e.g., chat messages, game state updates, system notifications).

        :param msg: Decoded JSON message (expected to be a dictionary)
        """
        if not isinstance(msg, dict):
            return

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
        
        func_handler = scenario_handlers.get(msg_type)
        return func_handler(**msg_content)

    def receive(self):
        """
        Continuously receive messages from the server.

        Handles TCP stream behavior by buffering incoming data and
        extracting complete JSON messages delimited by newline characters.
        """
        buffer = ""

        while True:
            try:
                data = self.client.recv(1024)

                # Server closed the connection
                if not data:
                    break

                # Append decoded data to buffer
                buffer += data.decode()

                # Process all complete messages in the buffer
                while "\n" in buffer:
                    raw_msg, buffer = buffer.split("\n", 1)
                    try:
                        msg = json.loads(raw_msg)
                        self.process_msg(msg)
                    except json.JSONDecodeError:
                        continue


            except Exception as error:
                print("Receive error:", error)
                break

    def write(self):
        """
        Continuously read user input and send messages to the server.

        Runs in a non-daemon thread so the client remains alive
        while waiting for user input.
        """
        while True:
            message = input("Enter a message: ")

            msg = {
                "type": self.mode,
                "payload": {
                    "name": self.name,
                    "message": message,
                }
            }

            # Add newline delimiter for server-side message framing
            data = json.dumps(msg) + "\n"
            self.client.sendall(data.encode())

    def start(self):
        """
        Connect to the server and start send/receive threads.
        """
        self.client.connect((self.host, self.port))
        print("Connected to server")

        # Background thread for receiving messages
        threading.Thread(target=self.receive, daemon=True).start()

        # Foreground thread for user input (keeps program alive)
        threading.Thread(target=self.write, daemon=False).start()


# Entry point for manual testing
if __name__ == "__main__":
    client = ClientNetwork(name="Client1")
    client.start()
