#!/bin/bash

# Define variables
INSTALL_DIR="/opt/Server"
SERVICE_FILE="/etc/systemd/system/server.service"
PYTHON_SCRIPT="$INSTALL_DIR/server.py"
VENV_DIR="$INSTALL_DIR/venv"

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Step 1: Create the installation directory
mkdir -p $INSTALL_DIR
echo "Created installation directory: $INSTALL_DIR"

# Step 2: Copy server.py to the installation directory
if [ -f /home/desent/Server/server.py ]; then
  cp /home/desent/Server/server.py $INSTALL_DIR/
  echo "Copied server.py to $INSTALL_DIR."
else
  echo "Error: /home/desent/Server/server.py not found!"
  exit 1
fi

# Step 3: Set up a virtual environment and install dependencies
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
echo "Created virtual environment in $VENV_DIR."

# Install dependencies if requirements.txt exists
if [ -f /home/desent/Server/requirements.txt ]; then
  cp /home/desent/Server/requirements.txt $INSTALL_DIR/
  pip install -r $INSTALL_DIR/requirements.txt
  echo "Installed Python dependencies."
else
  echo "No requirements.txt found. Skipping dependency installation."
fi

# Step 4: Create the systemd service file
cat << EOL > $SERVICE_FILE
[Unit]
Description=Python Server Service
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python3 $PYTHON_SCRIPT
WorkingDirectory=$INSTALL_DIR
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

# Set permissions and reload systemd
chmod 644 $SERVICE_FILE
systemctl daemon-reload
echo "Created systemd service file at $SERVICE_FILE."

# Step 5: Start and enable the service
systemctl start server.service
systemctl enable server.service
echo "Started and enabled server service."

echo "Installation complete. To manage the service, use:"
echo "  sudo systemctl start server.service"
echo "  sudo systemctl stop server.service"
echo "  sudo systemctl status server.service"
