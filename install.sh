#!/bin/bash
set -e

echo "=== S h a y d Z Super Monitor Full Install ==="

sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv python3-pil python3-numpy python3-flask python3-requests python3-feedparser raspi-config libopenjp2-7 libtiff5

echo "[*] Enabling SPI..."
sudo raspi-config nonint do_spi 0

echo "[*] Cloning Waveshare e-Paper lib (skip if already done)..."
if [ ! -d /opt/e-Paper ]; then
  sudo git clone https://github.com/waveshare/e-Paper.git /opt/e-Paper
fi

# Avoid recursive copy if already in /opt/shaydz
SCRIPT_DIR=$(pwd)
if [ "$SCRIPT_DIR" != "/opt/shaydz" ]; then
  echo "[*] Setting up ShaydZ project in /opt/shaydz..."
  sudo mkdir -p /opt/shaydz
  sudo cp -r ./* /opt/shaydz/
  cd /opt/shaydz
else
  echo "[*] Already in /opt/shaydz, skipping copy."
fi

echo "[*] Creating Python venv for ShaydZ..."
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[*] Creating systemd service..."
sudo tee /etc/systemd/system/shaydz.service > /dev/null << EOF
[Unit]
Description=ShaydZ Super Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/shaydz
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/shaydz/venv/bin/python3 /opt/shaydz/shaydz.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable shaydz
sudo systemctl restart shaydz

IPADDR=$(hostname -I | awk '{print $1}')
echo "=== Installation complete! S h a y d Z will run on boot and is available on your e-paper display and at http://$IPADDR:5001 ==="
