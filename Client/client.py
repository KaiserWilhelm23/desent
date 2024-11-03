import sys
import asyncio
import websockets
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCursor
from queue import Queue
from threading import Thread

# Function to display messages in the chat window
async def print_message(chat_display, message, color="white"):
    chat_display.setTextColor(QColor(color))
    chat_display.append(message)
    chat_display.setTextColor(QColor("white"))
    chat_display.moveCursor(QTextCursor.MoveOperation.End)

# Function to handle the connection and communication with the server
async def connect_to_server(string1, username, chat_display, message_queue):
    uri = f"wss://{string1}.ngrok-free.app"
    try:
        async with websockets.connect(uri) as websocket:
            await print_message(chat_display, f"Connected to {uri}\n", color="green")
            await websocket.send(username)  # Send username to server

            # Start listening to server messages in a separate task
            receive_task = asyncio.create_task(receive_messages(websocket, chat_display))

            while True:
                message = await asyncio.to_thread(message_queue.get)
                if message.lower() == '/exit':
                    await websocket.close()
                    break
                await websocket.send(message)
                await print_message(chat_display, f"You: {message}", color="cyan")

            # Wait until the receive task is done (e.g., on disconnect)
            await receive_task

    except websockets.exceptions.ConnectionClosedError as e:
        await print_message(chat_display, f"WebSocket closed. Code: {e.code}\n", color="red")
    except websockets.exceptions.WebSocketException as e:
        await print_message(chat_display, f"WebSocket error: {e}\n", color="red")
    except Exception as e:
        await print_message(chat_display, f"Unexpected error: {e}\n", color="red")

# Separate coroutine to receive messages continuously
async def receive_messages(websocket, chat_display):
    try:
        while True:
            incoming_message = await websocket.recv()
            await print_message(chat_display, incoming_message, color="yellow")
    except websockets.exceptions.ConnectionClosedError:
        await print_message(chat_display, "Disconnected from server.\n", color="red")
    except Exception as e:
        await print_message(chat_display, f"Error receiving messages: {e}\n", color="red")

# Start the chat in a separate thread
def start_chat(string1, username, chat_display, message_queue):
    asyncio.run(connect_to_server(string1, username, chat_display, message_queue))

# Function to handle sending messages
def send_message(input_field, message_queue):
    message = input_field.text()
    if message.strip():
        input_field.clear()
        message_queue.put(message)

# Run the asyncio event loop in a separate thread
def run_event_loop():
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_forever()

# PyQt6 Application Class
class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("DeSent Chat")
        self.setGeometry(100, 100, 600, 500)

        # Dark mode styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2e2e2e;
            }
            QLabel, QTextEdit, QLineEdit, QPushButton {
                color: #ffffff;
                font-size: 14px;
                font-family: Arial;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #5c5c5c;
                padding: 5px;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #5c5c5c;
                padding: 5px;
            }
            QPushButton {
                background-color: #3e3e3e;
                border: 1px solid #5c5c5c;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #5e5e5e;
            }
        """)

        # Main widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout(central_widget)

        # Ngrok string and name inputs
        self.string_label = QLabel("Enter Ngrok String:")
        self.string_input = QLineEdit()
        layout.addWidget(self.string_label)
        layout.addWidget(self.string_input)

        self.name_label = QLabel("Enter Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.start_connection)
        layout.addWidget(self.connect_button)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Horizontal layout for message input and send button
        message_layout = QHBoxLayout()
        
        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(lambda: send_message(self.message_input, self.message_queue))
        message_layout.addWidget(self.message_input)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(lambda: send_message(self.message_input, self.message_queue))
        message_layout.addWidget(self.send_button)

        # Add the message_layout to the main layout
        layout.addLayout(message_layout)

        # Message queue for handling messages
        self.message_queue = Queue()

    # Start chat connection
    def start_connection(self):
        string1 = self.string_input.text()
        username = self.name_input.text()
        if string1 and username:
            # Run the chat connection in a separate thread
            Thread(target=start_chat, args=(string1, username, self.chat_display, self.message_queue)).start()

# Run the application
app = QApplication(sys.argv)
chat_client = ChatClient()

# Start asyncio event loop in a separate thread
Thread(target=run_event_loop, daemon=True).start()

chat_client.show()
sys.exit(app.exec())
