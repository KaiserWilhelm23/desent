import asyncio
import websockets
import datetime
from colorama import Fore
from pyfiglet import Figlet
from pyngrok import ngrok
import sys
import subprocess
import os


# Dedicated to the person who got me into coding, Regina... 

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

# Initialize figlet font for title
f = Figlet(font='slant')
print(f.renderText('DeSent Server'))

# Function to load or prompt for ngrok auth token
def get_ngrok_auth_token():
    auth_file = "AUTH.txt"
    if os.path.exists(auth_file):
        # Read token from AUTH.txt if it exists
        with open(auth_file, "r") as f:
            auth_token = f.read().strip()
        print(Fore.GREEN + "Loaded ngrok auth token from AUTH.txt" + Fore.RESET)
    else:
        # Prompt user for token if AUTH.txt does not exist
        auth_token = input("Enter your ngrok auth token: ").strip()
        # Write token to AUTH.txt for future use
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

# Dictionary to store connected clients
clients = {}

# Function to handle each client connection
async def handle_client(websocket, path):
    try:
        # Receive the user's name when they first connect
        name = await websocket.recv()
        
        # Check for duplicate name in clients dictionary
        if name in clients:
            await websocket.send("Name already taken. Please choose another name.")
            print(Fore.YELLOW + f"Duplicate name attempted: {name}" + Fore.RESET)
            return
        else:
            clients[name] = websocket

        # Notify other clients that a new user has joined
        for client_name, client_ws in clients.items():
            if client_name != name:
                await client_ws.send(f"{name} has joined the chat")
        print(Fore.MAGENTA + f"{name} has joined the chat" + Fore.RESET)

        # Continuously listen for messages from the client
        async for message in websocket:
            if not message.strip():
                # Skip empty messages
                continue
            
            # Format the message with date/time and user name
            formatted_message = f"{name}: {message}"
            print(Fore.CYAN + formatted_message + Fore.RESET)

            # Broadcast the message to all other clients
            for client_name, client_ws in clients.items():
                if client_name != name:
                    try:
                        await client_ws.send(formatted_message)
                    except websockets.exceptions.ConnectionClosedError:
                        # Handle disconnected client
                        print(Fore.YELLOW + f"{client_name} has disconnected unexpectedly." + Fore.RESET)
                        clients.pop(client_name, None)

    except websockets.exceptions.ConnectionClosedError as e:
        print(Fore.RED + f"Connection error with {name}: {e}" + Fore.RESET)
    except Exception as e:
        print(Fore.RED + f"Unexpected error in handle_client: {e}" + Fore.RESET)
    finally:
        # Remove the client from the dictionary when they disconnect
        clients.pop(name, None)
        print(Fore.MAGENTA + f"{name} has left the chat" + Fore.RESET)
        for client_name, client_ws in clients.items():
            await client_ws.send(f"{name} has left the chat")

# Main function to start the server
async def main():
    print("Starting DeSent Server...")

    # Start ngrok tunnel on port 8765 for WebSocket compatibility
    try:
        http_tunnel = ngrok.connect(8765, "http")
        public_url = http_tunnel.public_url.replace("http://", "ws://").replace("https://", "wss://")
        print(Fore.GREEN + f"Server is publicly accessible at: {public_url}" + Fore.RESET)
    except Exception as e:
        print(Fore.RED + f"Error starting ngrok tunnel: {e}" + Fore.RESET)
        return

    # Start WebSocket server
    try:
        server = await websockets.serve(handle_client, "localhost", 8765, ping_timeout=None)
        print(Fore.GREEN + "WebSocket server started on ws://localhost:8765" + Fore.RESET)
        await server.wait_closed()
    except Exception as e:
        print(Fore.RED + f"Error starting WebSocket server: {e}" + Fore.RESET)

# Run the server
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(Fore.YELLOW + "Server interrupted by user" + Fore.RESET)
except Exception as e:
    print(Fore.RED + f"Unexpected error in main execution: {e}" + Fore.RESET)
