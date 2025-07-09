#!/bin/bash
set -e

echo "=== S h a y d Z Super Monitor Full Install ==="

sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv python3-pil python3-numpy python3-flask python3-requests python3-feedparser raspi-config

echo "[*] Enabling SPI..."
sudo raspi-config nonint do_spi 0

echo "[*] Cloning Waveshare e-Paper lib (skip if already done)..."
if [ ! -d /opt/e-Paper ]; then
  sudo git clone https://github.com/waveshare/e-Paper.git /opt/e-Paper
fi

echo "[*] Setting up ShaydZ project in /opt/shaydz..."
sudo mkdir -p /opt/shaydz
sudo cp -r ./* /opt/shaydz/
cd /opt/shaydz

echo "[*] Creating Python venv for ShaydZ..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[*] Creating systemd service..."
sudo tee /etc/systemd/system/shaydz.service > /dev/null << EOF
[Unit]
Description=ShaydZ Super Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shaydz
ExecStart=/opt/shaydz/venv/bin/python3 /opt/shaydz/shaydz.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable shaydz
sudo systemctl restart shaydz

echo "=== Installation complete! ShaydZ will run on boot and is available on your e-paper display and at http://<your-pi-ip>:5001 ==="
