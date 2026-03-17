# Remote Device Control and Monitoring System

A secure socket-based system that allows a central server to remotely monitor and control multiple IoT devices deployed across different locations.
This project demonstrates **TCP communication, TLS encryption, authentication, real-time monitoring, remote command execution, and latency analysis.**

## Features

* Secure communication using TLS/SSL
* Device authentication using secret token
* Remote command execution
* Real-time system monitoring
* Multi-device support
* Acknowledgment with latency measurement
* Threaded server for concurrent clients

---

## System Architecture

Server acts as a central controller while multiple client devices connect securely.

```
        ┌───────────────┐
        │   SERVER      │
        │ Controller    │
        └──────┬────────┘
               │ TLS (secure)
     ┌─────────┼─────────┐
     │         │         │
 ┌────────┐ ┌────────┐ ┌────────┐
 │Device1 │ │Device2 │ │Device3 │
 │Client  │ │Client  │ │Client  │
 └────────┘ └────────┘ └────────┘
```

---

## How It Works

### Connection & Authentication

1. Client connects to server using TLS
2. Client sends REGISTER message with device ID
3. Server requests authentication
4. Client sends secret token
5. Server verifies and accepts connection

---

### Monitoring

Each client periodically sends:

* CPU usage
* Memory usage
* Disk usage
* Timestamp

Server displays real-time device status.

---

### Remote Control

Server operator can send commands such as:

* LED_ON
* LED_OFF

Client executes the command and sends acknowledgment.

---

### Latency Analysis

Each command includes a timestamp.
Server calculates the time taken for execution.

---

## Technologies Used

* Python
* Socket Programming (TCP)
* SSL/TLS Encryption
* Multithreading
* JSON Messaging
* psutil (system monitoring)

---

## Project Structure

```
Remote-Device-control-and-monitoring-system/
│
├── server/
│   ├── server.py
│   ├── server.crt
│   └── server.key
│
├── client/
│   └── client.py
│
└── README.md
```

---

## Requirements

Install dependencies:

```
pip install psutil
```

---

## How to Run

### 1️. Start Server

```
cd server
python server.py
```

---

### 2️. Start Client Devices

Open new terminals:

```
cd client
python client.py
```

Enter unique device ID when prompted.

---

### 3️. Send Commands from Server

Follow on-screen prompts to send commands to connected devices.

---

## Security Notes

* Communication is encrypted using TLS
* Only devices with correct authentication token can connect
* Prevents unauthorized control of devices

---

## Applications

* IoT device management
* Smart home control systems
* Industrial monitoring
* Remote server management
* Edge device supervision

---

## Author

Project developed as part of academic coursework.

---

## 📜 License

For educational use only.
