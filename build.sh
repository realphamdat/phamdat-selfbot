#!/bin/bash
set -e

echo "Downloading Chrome..."
curl -L -o chrome.zip "https://storage.googleapis.com/chrome-for-testing-public/152.0.7977.54/linux64/chrome-linux64.zip"
unzip -q chrome.zip
rm chrome.zip
chmod +x chrome-linux64/chrome

echo "Installing Python dependencies..."
pip install -r requirements.txt