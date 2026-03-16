import socket
import ssl
import threading
import json
import time

HOST = "0.0.0.0"
PORT = 5000
AUTH_TOKEN = "MY_SECRET_KEY"

clients = {}
lock = threading.Lock()
pause_print = False


def handle_client(conn, addr):

    global pause_print
    device_id = None

    try:
        data = conn.recv(4096).decode()
        msg = json.loads(data)

        if msg["type"] != "REGISTER":
            conn.close()
            return

        device_id = msg["device_id"]

        conn.send(b"AUTH_REQUEST")

        token = conn.recv(1024).decode()

        if token != AUTH_TOKEN:
            conn.send(b"AUTH_FAILED")
            conn.close()
            return

        conn.send(b"AUTH_SUCCESS")

        with lock:
            clients[device_id] = conn

        print(f"[CONNECTED] {device_id} from {addr}")

        while True:

            data = conn.recv(4096)

            if not data:
                break

            message = json.loads(data.decode())

            if message["type"] == "STATUS":

                if not pause_print:
                    print(
                        f"[STATUS] {device_id} CPU:{message['cpu']} "
                        f"MEM:{message['memory']} DISK:{message['disk']}"
                    )

            elif message["type"] == "ACK":

                latency = time.time() - message["sent_time"]

                print(
                    f"[ACK] {device_id} executed {message['command']} "
                    f"Latency: {latency:.4f} sec"
                )

    except Exception as e:
        print("[ERROR]", e)

    finally:

        with lock:
            if device_id in clients:
                del clients[device_id]

        conn.close()

        print(f"[DISCONNECTED] {device_id}")


def send_command():

    global pause_print

    while True:

        with lock:
            device_list = list(clients.keys())

        if not device_list:
            time.sleep(2)
            continue

        pause_print = True

        print("\nConnected devices:", device_list)

        choice = input("Send command? (y/n): ")

        if choice.lower() != "y":
            pause_print = False
            continue

        device = input("Device ID: ")
        command = input("Command (LED_ON / LED_OFF): ")

        with lock:

            if device not in clients:
                print("Device not found")
                pause_print = False
                continue

            msg = {
                "type": "COMMAND",
                "command": command,
                "sent_time": time.time()
            }

            try:
                clients[device].send(json.dumps(msg).encode())
                print("[COMMAND SENT]")

            except Exception as e:
                print("[SEND ERROR]", e)

        pause_print = False


def start_server():

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("server.crt", "server.key")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((HOST, PORT))
    server_socket.listen(5)

    print("[SERVER STARTED] Secure TLS server running")

    threading.Thread(target=send_command, daemon=True).start()

    while True:

        client_socket, addr = server_socket.accept()

        secure_conn = context.wrap_socket(client_socket, server_side=True)

        threading.Thread(
            target=handle_client,
            args=(secure_conn, addr),
            daemon=True
        ).start()


if __name__ == "__main__":
    start_server()