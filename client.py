import asyncio
import websockets
from colorama import Fore
import sys
from pyfiglet import Figlet

f = Figlet(font='slant')
print(f.renderText('DeSent'))

async def send_message(websocket, username):
  while True:
    loop = asyncio.get_event_loop()
    message = await loop.run_in_executor(None, input)

    if message.lower() == '/exit':
      await websocket.close()
      break
    await websocket.send(message)


async def receive_messages(websocket):
  async for message in websocket:
    print(f"\n{message}")
    sys.stdout.write("")
    sys.stdout.flush()


async def main():
  string1 = input("Please Enter a Ngrog String: ")
  uri = f"wss://{string1}.ngrok-free.app"  # Change this to the address of your WebSocket server

  try:
    async with websockets.connect(uri) as websocket:
      print(Fore.GREEN + f"Connection to {uri} successful!" + Fore.RESET)
      username = input("Enter your name: " + Fore.BLUE)
      await websocket.send(username)
      print(Fore.GREEN + "Ready! Just Start Typing!" + Fore.RESET)

      # Start tasks for sending and receiving messages
      send_task = asyncio.create_task(send_message(websocket, username))
      receive_task = asyncio.create_task(receive_messages(websocket))

      # Wait for both tasks to complete
      await asyncio.gather(send_task, receive_task)

  except websockets.exceptions.ConnectionClosedError as e:
    print(Fore.RED +
          f"WebSocket connection closed unexpectedly. Code: {e.code}" +
          Fore.RESET)
  except websockets.exceptions.WebSocketException as e:
    print(Fore.RED + f"WebSocket error: {e}" + Fore.RESET)
    await main() 
  except Exception as e:
    print(Fore.RED + f"An unexpected error occurred: {e}" + Fore.RESET)


if __name__ == "__main__":
  asyncio.run(main())
