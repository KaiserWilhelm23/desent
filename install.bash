#!/bin/bash

# Check if the script is running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 
    exit 1
fi

# Update the package index and install necessary packages
apt update
apt install -y wget unzip

# Download and extract Grok
wget https://github.com/logstash-plugins/logstash-patterns-core/archive/master.zip -O grok_patterns.zip
unzip grok_patterns.zip -d /usr/share/grok

# Clean up
rm grok_patterns.zip

echo "Grok installed successfully at /usr/share/grok"
