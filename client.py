import socket
import threading

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

user_id = None
user_ip = None
user_port = None
online_users = {}
current_room = None

def listen_for_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(message)
                if message.startswith("Users:"):
                    update_online_users(message)
            else:
                break
        except Exception as e:
            print(f"Error receiving messages: {e}")
            break

def receive_messages():
    global user_ip, user_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((user_ip, user_port))
        s.listen()
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_incoming_message, args=(conn, addr)).start()

def handle_incoming_message(conn, addr):
    with conn:
        try:
            message = conn.recv(1024).decode()
            print(message)
        except Exception as e:
            print(f"Error handling incoming message from {addr}: {e}")

def send_direct_message(target_id, message):
    if target_id in online_users:
        target_ip, target_port = online_users[target_id]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_ip, target_port))
            s.sendall(f"Message from {user_id}: {message}".encode())
    else:
        print(f"User {target_id} not found")

def update_online_users(message):
    global online_users
    users_list = message[len("Users: "):].strip("[]").split(", ")
    online_users = {}
    for entry in users_list:
        if entry:
            user, ip, port = entry.split()
            online_users[user] = (ip, int(port))
    print(f"Updated online users: {online_users}")

def main():
    global user_id, user_ip, user_port, online_users, current_room

    user_id = input("Enter your user ID: ")
    user_ip = socket.gethostbyname(socket.gethostname())
    user_port = int(input("Enter your port: "))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(f"LOGIN {user_id} {user_ip} {user_port}".encode())

        threading.Thread(target=listen_for_messages, args=(s,)).start()
        threading.Thread(target=receive_messages).start()

        while True:
            msg = input()
            if msg.lower() == 'logout':
                s.sendall(f"LOGOUT {user_id}".encode())
                break
            elif msg.lower() == 'get users':
                s.sendall("GET_USERS".encode())
            elif msg.lower().startswith('create room'):
                room_name = msg.split(' ', 2)[2]
                s.sendall(f"CREATE_ROOM {room_name}".encode())
                current_room = room_name
            elif msg.lower().startswith('invite'):
                room_name, target_id = msg.split(' ', 2)[1:]
                s.sendall(f"INVITE {room_name} {target_id}".encode())
            elif msg.lower().startswith('send'):
                _, room_name, message = msg.split(' ', 2)
                s.sendall(f"SEND {room_name} {message}".encode())
            else:
                if current_room:
                    s.sendall(f"SEND {current_room} {msg}".encode())
                else:
                    try:
                        target_id, message = msg.split(':', 1)
                        send_direct_message(target_id.strip(), message.strip())
                    except ValueError:
                        print("Invalid message format. Use 'user_id: message'")

if __name__ == "__main__":
    main()
