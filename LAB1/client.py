
import socket
import threading

HOST = "127.0.0.1"
PORT = 5000


def receive_messages(sock):
    try:
        reader = sock.makefile("r", encoding="utf-8")

        for line in reader:
            print("\n" + line.rstrip("\r\n"))
            print("> ", end="", flush=True)

    except (ConnectionError, OSError):
        pass

    finally:
        print("\n[CLIENT] Connection closed.")


def main():
    try:
        sock = socket.create_connection((HOST, PORT))

        name = input("Enter your name: ")
        sock.sendall((name + "\n").encode("utf-8"))

        receiver = threading.Thread(
            target=receive_messages,
            args=(sock,),
            daemon=True
        )

        receiver.start()

        print("Connected! Type messages. Type /quit to leave.")

        while True:
            message = input("> ")

            sock.sendall((message + "\n").encode("utf-8"))

            if message == "/quit":
                break

    except (ConnectionError, OSError) as e:
        print(f"[ERROR] {e}")

    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
