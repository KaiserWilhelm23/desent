import asyncio
import websockets
from colorama import Fore
from pyfiglet import Figlet
from pyngrok import ngrok
import requests
import sys
import subprocess
import os
import json
import time
import getpass
from pathlib import Path

# This code is dedicated to Reginia...

# Function to check and install dependencies
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check and install required packages
install_and_import("websockets")
install_and_import("colorama")
install_and_import("pyfiglet")
install_and_import("pyngrok")
install_and_import("requests")

# Initialize figlet font for title
f = Figlet(font='slant')
print(f.renderText('DeSent Server'))

# Configuration file path
CONFIG_FILE = "config.json"

# Function to load or create a config file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        print(Fore.GREEN + "Loaded configuration from config.json" + Fore.RESET)
    else:
        # Prompt the user for input to create a config file
        print(Fore.YELLOW + "No config file found. Creating a new one." + Fore.RESET)
        
        post_response = input("Do you want the server Public? (y/n): ").strip().lower()
        post = True if post_response == "y" else False
        
        name = input("Enter the name of the server (if public): ").strip() if post else ""
        subdomain = input("Enter subdomain (leave blank for random if public, or skip if private): ").strip() if post else ""
        region = input("Enter region (required if public): ").strip() if post else ""

        # Create the default config with user input
        config = {
            "POST": post,
            "NAME": name,
            "subdomain": subdomain if subdomain else None,  # Skip prompt by setting a default or "None" for random subdomain
            "region": region
        }
        save_config(config)
    return config

# Function to save the configuration to the config.json file
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print(Fore.GREEN + "Configuration saved to config.json" + Fore.RESET)

# Load initial config
config = load_config()

# Function to load or prompt for ngrok auth token
def get_ngrok_auth_token():
    auth_file = "AUTH.txt"
    if os.path.exists(auth_file):
        with open(auth_file, "r") as f:
            auth_token = f.read().strip()
        print(Fore.GREEN + "Loaded ngrok auth token from AUTH.txt" + Fore.RESET)
    else:
        auth_token = input("Enter your ngrok auth token: ").strip()
        with open(auth_file, "w") as f:
            f.write(auth_token)
        print(Fore.GREEN + "Ngrok auth token saved to AUTH.txt" + Fore.RESET)
    return auth_token

# Set ngrok authentication token
try:
    auth_token = get_ngrok_auth_token()
    ngrok.set_auth_token(auth_token)
except Exception as e:
    print(Fore.RED + f"Error setting ngrok auth token: {e}" + Fore.RESET)

# Function to publish or update server data in Firebase
def publish_server(name, identifier, region):
    url = f'https://desent-public-servers-default-rtdb.firebaseio.com/desent-public-servers/{name}.json'
    data = {"name": name, "url": identifier, "region": region}

    response = requests.get(url)
    if response.status_code == 200 and response.json() is not None:
        print(Fore.YELLOW + f"Server name '{name}' exists, updating entry." + Fore.RESET)
    else:
        print(Fore.GREEN + f"Adding new server entry: {name}" + Fore.RESET)

    result = requests.put(url, json=data)
    if result.status_code == 200:
        print(Fore.GREEN + f"Server '{name}' published/updated successfully." + Fore.RESET)
    else:
        print(Fore.RED + f"Error publishing server '{name}': {result.text}" + Fore.RESET)

# Function to remove server listing from Firebase
def remove_server(name):
    url = f'https://desent-public-servers-default-rtdb.firebaseio.com/desent-public-servers/{name}.json'
    result = requests.delete(url)
    if result.status_code == 200:
        print(Fore.GREEN + f"Server '{name}' removed successfully." + Fore.RESET)
    else:
        print(Fore.RED + f"Error removing server '{name}': {result.text}" + Fore.RESET)

# Dictionary to store connected clients
clients = {}

# Function to handle each client connection
async def handle_client(websocket, path):  # path added
    try:
        name = await websocket.recv()
        if name in clients:
            await websocket.send("Name already taken. Please choose another name.")
            return
        else:
            clients[name] = websocket
        for client_name, client_ws in clients.items():
            if client_name != name:
                await client_ws.send(f"{name} has joined the chat")

        async for message in websocket:
            formatted_message = f"{name}: {message}"
            print(formatted_message)  # Display each message in the console
            for client_name, client_ws in clients.items():
                if client_name != name:
                    await client_ws.send(formatted_message)
    except Exception as e:
        print(Fore.RED + f"Unexpected error in handle_client: {e}" + Fore.RESET)
    finally:
        clients.pop(name, None)
        for client_name, client_ws in clients.items():
            await client_ws.send(f"{name} has left the chat")

# Main function to start the server
async def start_server():
    subdomain = config["subdomain"] or ""
    region = config["region"] or ""
    server_name = config["NAME"] or ""

    # Update config with user input if needed
    config.update({"subdomain": subdomain, "region": region, "NAME": server_name})
    save_config(config)

    ngrok_config = {"addr": 8765, "bind_tls": True}
    if subdomain:
        ngrok_config["subdomain"] = subdomain

    try:
        http_tunnel = ngrok.connect(**ngrok_config)
        public_url = http_tunnel.public_url.replace("http://", "ws://").replace("https://", "wss://")
        identifier = public_url.split("//")[1].split(".")[0]
        print(Fore.GREEN + f"Server identifier: {identifier}" + Fore.RESET)

        if config.get("POST"):
            publish_server(server_name, identifier, region)

        # Start WebSocket server
        server = await websockets.serve(handle_client, "localhost", 8765, ping_timeout=None)
        print(Fore.GREEN + "WebSocket server started on ws://localhost:8765" + Fore.RESET)
        await server.wait_closed()
    except Exception as e:
        print(Fore.RED + f"Error starting ngrok or WebSocket server: {e}" + Fore.RESET)

# Function to create systemd service file with automation
def create_systemd_service():
    script_path = Path(__file__).resolve()
    working_dir = script_path.parent
    username = getpass.getuser()

    service_content = f"""[Unit]
Description=DeSent Server Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 {script_path}
WorkingDirectory={working_dir}
Restart=always
User={username}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/etc/systemd/system/desent-server.service")

    try:
        with service_path.open("w") as f:
            f.write(service_content)
    except PermissionError:
        print(Fore.YELLOW + "Permission required to write service file. Using sudo..." + Fore.RESET)
        try:
            subprocess.run(
                ["sudo", "tee", str(service_path)],
                input=service_content.encode(),
                check=True
            )
            print(Fore.GREEN + "Systemd service file created successfully with elevated permissions." + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"Failed to create systemd service file with sudo: {e}" + Fore.RESET)
            return

    print(Fore.GREEN + "Systemd service file created at /etc/systemd/system/desent-server.service" + Fore.RESET)
    print(Fore.YELLOW + "Run 'sudo systemctl enable desent-server' to start on boot and 'sudo systemctl start desent-server' to start now." + Fore.RESET)

# Run the server with automatic restart on crash
while True:
    try:
        asyncio.run(start_server())
    except Exception as e:
        print(Fore.RED + f"Server crashed with error: {e}. Restarting..." + Fore.RESET)
        time.sleep(5)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "Server interrupted by user. Exiting..." + Fore.RESET)
        if input("Remove server from listing? (y/n): ").strip().lower() == "y":
            remove_server(config["NAME"])
        if input("Set up automatic start on boot? (y/n): ").strip().lower() == "y":
            create_systemd_service()
        break
