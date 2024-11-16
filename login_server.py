import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

online_users = {}
chat_rooms = {}

def handle_client(conn, addr):
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            command, *params = data.split()
            if command == "LOGIN":
                user_id, user_ip, user_port = params
                online_users[user_id] = (user_ip, int(user_port))
                save_users()
                conn.sendall(f"Users: {list_online_users()}".encode())
            elif command == "LOGOUT":
                user_id = params[0]
                if user_id in online_users:
                    del online_users[user_id]
                    save_users()
                conn.sendall(f"{user_id} logged out".encode())
            elif command == "GET_USERS":
                conn.sendall(f"Users: {list_online_users()}".encode())
            elif command == "CREATE_ROOM":
                room_name = params[0]
                if room_name not in chat_rooms:
                    chat_rooms[room_name] = set()
                conn.sendall(f"Room {room_name} created".encode())
            elif command == "INVITE":
                room_name, user_id = params
                if room_name in chat_rooms and user_id in online_users:
                    chat_rooms[room_name].add(user_id)
                    conn.sendall(f"{user_id} invited to {room_name}".encode())
            elif command == "SEND":
                room_name = params[0]
                message = ' '.join(params[1:])
                if room_name in chat_rooms:
                    broadcast_message(room_name, message)

def broadcast_message(room_name, message):
    if room_name in chat_rooms:
        for user_id in chat_rooms[room_name]:
            user_ip, user_port = online_users[user_id]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((user_ip, user_port))
                s.sendall(message.encode())

def save_users():
    with open("users.txt", "w") as f:
        for user_id, (user_ip, user_port) in online_users.items():
            f.write(f"{user_id} {user_ip} {user_port}\n")

def list_online_users():
    return ', '.join([f"{user_id} {ip} {port}" for user_id, (ip, port) in online_users.items()])

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server started at {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()
