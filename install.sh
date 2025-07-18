#!/bin/bash
set -e

echo "=== S h a y d Z Super Monitor Production Install ==="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons"
   exit 1
fi

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3 python3-pip python3-venv python3-pil python3-numpy \
    python3-flask python3-requests python3-feedparser raspi-config libopenjp2-7 \
    libtiff5 nginx ufw fail2ban logrotate

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
  sudo chown -R $USER:$USER /opt/shaydz
else
  echo "[*] Already in /opt/shaydz, skipping copy."
fi

echo "[*] Creating Python venv for ShaydZ..."
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "[*] Setting up log rotation..."
sudo tee /etc/logrotate.d/shaydz > /dev/null << 'EOF'
/opt/shaydz/shaydz.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $(whoami) $(whoami)
    postrotate
        systemctl reload shaydz || true
    endscript
}
EOF

echo "[*] Configuring firewall..."
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 5001/tcp comment "ShaydZ Web UI"

echo "[*] Creating systemd service..."
sudo tee /etc/systemd/system/shaydz.service > /dev/null << EOF
[Unit]
Description=ShaydZ Super Monitor
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/opt/shaydz
Environment=PYTHONUNBUFFERED=1
Environment=FLASK_DEBUG=false
ExecStart=/opt/shaydz/venv/bin/python3 /opt/shaydz/shaydz.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=shaydz

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/shaydz
CapabilityBoundingSet=CAP_NET_RAW

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096
MemoryMax=512M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

echo "[*] Setting up fail2ban for web UI protection..."
sudo tee /etc/fail2ban/jail.d/shaydz.conf > /dev/null << 'EOF'
[shaydz]
enabled = true
port = 5001
filter = shaydz
logpath = /opt/shaydz/shaydz.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

sudo tee /etc/fail2ban/filter.d/shaydz.conf > /dev/null << 'EOF'
[Definition]
failregex = ^.*Login failed.*from.*<HOST>.*$
ignoreregex =
EOF

echo "[*] Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable shaydz
sudo systemctl start shaydz
sudo systemctl restart fail2ban

# Get IP address
IPADDR=$(hostname -I | awk '{print $1}')

echo "=== Production Installation Complete! ==="
echo "✓ ShaydZ Super Monitor is running as a systemd service"
echo "✓ Web UI available at: http://$IPADDR:5001"
echo "✓ Firewall configured and enabled"
echo "✓ Fail2ban protection active"
echo "✓ Log rotation configured"
echo "✓ Security hardening applied"
echo ""
echo "Service management commands:"
echo "  sudo systemctl status shaydz    # Check status"
echo "  sudo systemctl restart shaydz   # Restart service"
echo "  sudo systemctl stop shaydz      # Stop service"
echo "  sudo journalctl -u shaydz -f    # View logs"
echo ""
echo "First-time setup:"
echo "  1. Go to http://$IPADDR:5001"
echo "  2. Create your admin account"
echo "  3. Configure AI settings (optional)"
echo "  4. Monitor your network!"
