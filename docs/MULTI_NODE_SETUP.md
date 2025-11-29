# 🌍 Orbis Ethica: Multi-Node Setup Guide

This guide explains how to turn your single "Genesis Node" into a real 3-node network using your extra computers.

## Prerequisites
*   **Computer A (Genesis):** Already running (The one you are using now).
*   **Computer B & C (Peers):** Need Docker installed.
*   **Network:** All computers must be on the same Wi-Fi/LAN.

---

## Step 1: Find Genesis IP (Computer A)
We need the local IP address of your main computer so the others can find it.

**On Mac/Linux (Terminal):**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
*Look for something like `192.168.1.X` or `10.0.0.X`.*

**Let's assume the IP is:** `192.168.1.10`

---

## Step 2: Configure Computer B (Peer 1)

1.  **Clone the Code:** Copy the project folder to Computer B.
2.  **Create/Edit `.env` file:**
    Create a file named `.env` in the root folder with these settings:

```bash
# Identity
NODE_ID=node_bravo
KEY_PASSWORD=your_secret_password

# Network Configuration
NODE_HOST=0.0.0.0
NODE_PORT=6430
P2P_PORT=6430

# Connection to Genesis (REPLACE WITH COMPUTER A's IP)
SEED_NODES=192.168.1.10:6430

# API Keys (Optional for now)
GEMINI_API_KEY=
GROQ_API_KEY=
```

3.  **Run:**
    ```bash
    docker compose up --build
    ```

---

## Step 3: Configure Computer C (Peer 2)

1.  **Clone the Code:** Copy the project folder to Computer C.
2.  **Create/Edit `.env` file:**

```bash
# Identity
NODE_ID=node_charlie
KEY_PASSWORD=your_secret_password

# Network Configuration
NODE_HOST=0.0.0.0
NODE_PORT=6430
P2P_PORT=6430

# Connection to Genesis (REPLACE WITH COMPUTER A's IP)
SEED_NODES=192.168.1.10:6430
```

3.  **Run:**
    ```bash
    docker compose up --build
    ```

---

## Step 4: Verify the Network 🚀

1.  Go back to **Computer A (Genesis)**.
2.  Open the **Dashboard** (`http://localhost:3000`).
3.  Look at the **"Network Status"** or **"Peers"** section.
4.  You should see **2 Active Peers** (`node_bravo` and `node_charlie`) connected!

### Troubleshooting
*   **Firewall:** If they don't connect, ensure Computer A allows incoming connections on port `6430`.
*   **Docker Network:** Ensure Docker is running in "Bridge" mode (default).
