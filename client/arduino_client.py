# ============================================================
# arduino_client.py — Arduino Bridge Client
# ============================================================
# This script runs on the laptop connected to the Arduino UNO.
# It does 3 things:
#   1. Connects to the central server over a secure TLS connection
#   2. Authenticates itself using a secret token
#   3. Waits for commands from the server and forwards them
#      to the Arduino via Serial (USB cable)
#
# Think of this script as a "translator" —
# it receives network commands and converts them into
# Serial signals the Arduino can understand.
# ============================================================

import socket       # For creating TCP network connections
import ssl          # For encrypting the connection with TLS
import json         # For encoding/decoding messages as JSON
import serial       # pyserial — for talking to Arduino over USB
import time         # For timestamps and sleep

# ── Configuration ───────────────────────────────────────────
SERVER_IP  = "10.56.56.71"              # IP address of the server laptop
WEB_UI_URL = "http://10.56.56.90:8080/ack"  # Web dashboard URL to report ACK latency
PORT       = 5000                       # Port the server listens on
AUTH_TOKEN = "MY_SECRET_KEY"            # Must match AUTH_TOKEN in server.py

# ── Device Identity ─────────────────────────────────────────
# Each Arduino client identifies itself with a unique name
# This name is used by the web UI to target specific devices
device_id = input("Enter Device ID: ")

# ── Serial Connection to Arduino ────────────────────────────
# Open a Serial connection to the Arduino UNO over USB
# 'COM5'  = the COM port Arduino is connected to on Windows
#           (check Device Manager -> Ports to find yours)
# 9600    = baud rate — speed of data transfer in bits per second
#           must match Serial.begin(9600) in the Arduino sketch
arduino = serial.Serial('COM5', 9600)

# Wait 2 seconds for the Arduino to finish resetting
# When a Serial connection opens, Arduino automatically resets
# If we don't wait, the first command might be sent too early
# and the Arduino won't be ready to receive it
time.sleep(2)

# ── SSL Context Setup ───────────────────────────────────────
# PROTOCOL_TLS_CLIENT = we are the client side of the TLS connection
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

# Disable hostname verification — normally TLS clients verify
# the server's certificate against a trusted Certificate Authority (CA)
# Since we use a self-signed certificate (not from a real CA),
# we disable these checks for local network use
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE
# Note: the connection is still fully ENCRYPTED — we just skip
# identity verification since it's a self-signed cert

# ── Connect to Server with TLS ──────────────────────────────
# IMPORTANT: We connect the raw TCP socket FIRST, then wrap with SSL
# This order is required on Windows — wrapping before connecting causes errors

# Step 1: Create a plain TCP socket (IPv4, TCP)
raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Step 2: Connect the raw socket to the server
raw_sock.connect((SERVER_IP, PORT))

# Step 3: Wrap the connected socket with TLS encryption
# This performs the TLS handshake — client and server agree on
# encryption keys so all further communication is encrypted
sock = context.wrap_socket(raw_sock)

print("[SSL] Connected securely to server")

# ── Step 1: Register with the Server ────────────────────────
# Send a REGISTER message to tell the server who we are
# The server uses device_id to identify and route commands to us
register = {
    "type": "REGISTER",
    "device_id": device_id
}
sock.send(json.dumps(register).encode())
# json.dumps() converts dict to JSON string
# .encode() converts string to bytes (required for socket.send)

# ── Step 2: Authentication Handshake ────────────────────────
# The server will now challenge us for a secret token

# Wait for AUTH_REQUEST from server
if sock.recv(1024) != b"AUTH_REQUEST":
    # If we don't get AUTH_REQUEST, something is wrong — exit
    exit()

# Send our secret token to the server
sock.send(AUTH_TOKEN.encode())

# Wait for AUTH_SUCCESS or AUTH_FAILED
if sock.recv(1024) != b"AUTH_SUCCESS":
    print("Auth failed")
    exit()   # Wrong token — server rejected us

print(f"[CONNECTED] {device_id}")

# ── Step 3: Listen for Commands ─────────────────────────────
# Now we're authenticated and registered.
# Enter an infinite loop waiting for commands from the server.
# The server will send a COMMAND message whenever the web UI
# clicks LED ON or LED OFF.
while True:

    # Wait to receive data from the server (up to 4096 bytes)
    data = sock.recv(4096)

    # If recv() returns empty bytes, the server disconnected
    if not data:
        break

    # Decode the JSON message
    message = json.loads(data.decode())

    # ── Handle COMMAND message ───────────────────────────────
    if message["type"] == "COMMAND":
        cmd = message["command"]   # e.g. "LED_ON" or "LED_OFF"
        print(f"[COMMAND RECEIVED] {cmd}")

        # ── Forward command to Arduino via Serial ────────────
        # Write the command string followed by newline to Serial port
        # The Arduino sketch reads until '\n' using readStringUntil('\n')
        # So "LED_ON\n" tells the Arduino to turn the LED on
        arduino.write((cmd + "\n").encode())

        # ── Send ACK back to server ──────────────────────────
        # ACK = Acknowledgement — confirms the command was received
        # and forwarded to the Arduino
        # sent_time is the original timestamp from when the server
        # sent the command — used to calculate round-trip latency
        ack = {
            "type":      "ACK",
            "device_id": device_id,
            "command":   cmd,
            "sent_time": message["sent_time"]   # Original timestamp preserved
        }
        sock.send(json.dumps(ack).encode())

        # Latency is calculated on the server side as:
        # latency = time.time() - message["sent_time"]
        # This tells us how long it took from sending the command
        # to receiving the ACK confirmation
