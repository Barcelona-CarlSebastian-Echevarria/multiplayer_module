import socket
import threading

nickname = input("Choose your nickname: ")

# The server's hostname or IP address
# Serve in cmd through 'ipconfig' and look for 'IPv4 Address'
HOST = ''  
# The port used by the server
PORT = 65432  

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

# Listening to Server and Sending Nickname
def receive():  
    while True:
        try:
            # Receive message from server
            message = client.recv(1024).decode('ascii')
            if message == 'NICK':
                client.send(nickname.encode('ascii'))
            else:
                print(message)
        except:
            # Close connection when error
            print("An error occurred!")
            client.close()
            break

# Writes a message
def write():    
    while True:
        message = f'{nickname}: {input("Enter a message: ")}'
        client.send(message.encode('ascii'))

def run():
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    write_thread = threading.Thread(target=write)
    write_thread.start()

run()

