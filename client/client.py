import socket
import ssl
import json
import time
import psutil
import threading

SERVER_IP = "127.0.0.1"
PORT = 5000
AUTH_TOKEN = "MY_SECRET_KEY"

device_id = input("Enter Device ID: ")


def send_status(sock):

    while True:

        status = {
            "type": "STATUS",
            "device_id": device_id,
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent,
            "timestamp": time.time()
        }

        try:
            sock.send(json.dumps(status).encode())

            print(
                f"[STATUS SENT] CPU:{status['cpu']} "
                f"MEM:{status['memory']} DISK:{status['disk']}"
            )

        except:
            break

        time.sleep(5)


def receive_messages(sock):

    while True:

        try:

            data = sock.recv(4096)

            if not data:
                break

            message = json.loads(data.decode())

            if message["type"] == "COMMAND":

                cmd = message["command"]

                print(f"[COMMAND RECEIVED] {cmd}")

                time.sleep(1)

                ack = {
                    "type": "ACK",
                    "device_id": device_id,
                    "command": cmd,
                    "sent_time": message["sent_time"]
                }

                sock.send(json.dumps(ack).encode())

        except:
            break


def main():

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    secure_socket = context.wrap_socket(raw_socket, server_hostname=SERVER_IP)

    secure_socket.connect((SERVER_IP, PORT))

    register = {
        "type": "REGISTER",
        "device_id": device_id
    }

    secure_socket.send(json.dumps(register).encode())

    if secure_socket.recv(1024) != b"AUTH_REQUEST":
        return

    secure_socket.send(AUTH_TOKEN.encode())

    if secure_socket.recv(1024) != b"AUTH_SUCCESS":
        print("Authentication failed")
        return

    print("[AUTH SUCCESS] Connected to server")

    threading.Thread(
        target=send_status,
        args=(secure_socket,),
        daemon=True
    ).start()

    receive_messages(secure_socket)


if __name__ == "__main__":
    main()