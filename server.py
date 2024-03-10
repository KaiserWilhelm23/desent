import asyncio
import websockets
import datetime
from colorama import Fore

from pyfiglet import Figlet

f = Figlet(font='slant')
print(f.renderText('DeSent Server'))

# Dictionary to store connected clients
clients = {}

async def handle_client(websocket, path):
    # Receive the user's name when they first connect
    name = await websocket.recv()
  
    # Check for duplicates in clients dictionary
    if name in clients:
      await websocket.send(Fore.RED + "Name already taken. Please choose another name." + Fore.RESET)
      return
    else:
      clients[name] = websocket

    # Notify other clients that a new user has joined
    for client, _ in clients.items():
        if client != websocket:
            await websocket.send(Fore.MAGENTA + f"{name} has joined the chat" + Fore.RESET)
            print(f"{name} has joined the chat")

    try:
        # Continuously listen for messages from the client
        async for message in websocket:
          if message == "":
            # Don't send empty messages
            continue
             

          else:
            # Format the message with date/time and user name
            formatted_message = Fore.BLUE + f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{name}]:" + Fore.RESET + f"{message}"
            print(formatted_message)

            # Broadcast the message to all other clients
            for client, _ in clients.items():
              if client != websocket:
                  try:
                      await client.send(formatted_message)
                  except websockets.exceptions.ConnectionClosedError:
                      # Remove disconnected clients
                      del clients[client]
                      await client.send(Fore.MAGENTA + f"{clients[client]} has left the chat" + Fore.RESET)
    finally:
        # Remove the client from the dictionary when they disconnect
        del clients[websocket]
        for client, _ in clients.items():
            await client.send(Fore.MAGENTA + f"{name} has left the chat" + Fore.RESET)

async def main():
    print("Started!")
    server = await websockets.serve(handle_client, "localhost", 8765, ping_timeout=None)

    # Start the WebSocket server
    await server.wait_closed()

asyncio.run(main())
