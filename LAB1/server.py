
import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

clients = {}
clients_lock = threading.Lock()

broadcast_mode = False
mode_lock = threading.Lock()


def send_message(conn, message):
    try:
        conn.sendall((message + "\n").encode("utf-8"))
        return True
    except OSError:
        return False


def broadcast(message):
    with clients_lock:
        connections = list(clients.items())

    for conn, name in connections:
        if not send_message(conn, message):
            remove_client(conn)


def remove_client(conn):
    with clients_lock:
        name = clients.pop(conn, None)

    if name:
        print(f"\n[DISCONNECTED] {name}")

    try:
        conn.close()
    except OSError:
        pass


def handle_client(conn, address):
    try:
        reader = conn.makefile("r", encoding="utf-8")

        name = reader.readline().strip()

        if not name:
            conn.close()
            return

        with clients_lock:
            clients[conn] = name

        print(f"\n[CONNECTED] {name} - {address}")
        send_message(conn, "[SERVER] Connected successfully.")

        while True:
            line = reader.readline()

            if not line:
                break

            message = line.rstrip("\r\n")

            if message == "/quit":
                break

            if not message:
                continue

            print(f"\n[PRIVATE MESSAGE] {name}: {message}")

            with mode_lock:
                current_mode = broadcast_mode

            if current_mode:
                broadcast(f"[CHAT] {name}: {message}")

    except (ConnectionError, OSError) as e:
        print(f"\n[ERROR] {address}: {e}")

    finally:
        remove_client(conn)


def server_console():
    global broadcast_mode

    print("\nServer Commands:")
    print("/mode       - Toggle broadcast mode")
    print("/list       - List connected clients")
    print("/reply NAME MESSAGE - Private reply")
    print("/broadcast MESSAGE  - Broadcast manually")
    print("Type any other message to broadcast.\n")

    while True:
        command = input("SERVER> ").strip()

        if not command:
            continue

        if command == "/mode":
            with mode_lock:
                broadcast_mode = not broadcast_mode
                current_mode = broadcast_mode

            if current_mode:
                print("[MODE] BROADCAST MODE ON")
                print("[MODE] Client messages will be visible to all clients.")
            else:
                print("[MODE] PRIVATE MODE ON")
                print("[MODE] Client messages are visible only to the server.")

        elif command == "/list":
            with clients_lock:
                names = list(clients.values())

            print("[CLIENTS]", names if names else "No connected clients")

        elif command.startswith("/reply "):
            parts = command.split(" ", 2)

            if len(parts) < 3:
                print("Usage: /reply NAME MESSAGE")
                continue

            target_name = parts[1]
            message = parts[2]

            with clients_lock:
                target = next(
                    (conn for conn, name in clients.items()
                     if name == target_name),
                    None
                )

            if target:
                if send_message(target, f"[SERVER PRIVATE]: {message}"):
                    print(f"[SENT] Private message to {target_name}")
                else:
                    print("[ERROR] Could not send message.")
            else:
                print("[ERROR] Client not found.")

        elif command.startswith("/broadcast "):
            message = command[len("/broadcast "):]
            broadcast(f"[SERVER BROADCAST]: {message}")
            print("[SENT] Broadcast to all clients.")

        else:
            broadcast(f"[SERVER BROADCAST]: {command}")
            print("[SENT] Broadcast to all clients.")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"[SERVER] Listening on {HOST}:{PORT}")
    print("[SERVER] Initial mode: PRIVATE")

    console_thread = threading.Thread(
        target=server_console,
        daemon=True
    )
    console_thread.start()

    try:
        while True:
            conn, address = server.accept()

            thread = threading.Thread(
                target=handle_client,
                args=(conn, address),
                daemon=True
            )
            thread.start()

    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")

    finally:
        with clients_lock:
            connections = list(clients.keys())

        for conn in connections:
            try:
                conn.close()
            except OSError:
                pass

        server.close()


if __name__ == "__main__":
    main()
