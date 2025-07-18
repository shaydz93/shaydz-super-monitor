# Production Deployment Guide

## Pre-Deployment Checklist

### System Requirements
- [ ] Raspberry Pi 3B+ or newer (or compatible Linux system)
- [ ] 8GB+ SD card with fresh Raspberry Pi OS
- [ ] Network connection (Wi-Fi or Ethernet)
- [ ] Optional: Waveshare 2.13" V3 e-Paper HAT

### Security Preparations
- [ ] Change default pi user password
- [ ] Enable SSH key authentication
- [ ] Update system packages
- [ ] Configure automatic security updates

## Production Installation

### 1. Initial System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Create dedicated user (optional but recommended)
sudo useradd -m -s /bin/bash shaydz
sudo usermod -aG sudo shaydz

# Switch to shaydz user
sudo su - shaydz
```

### 2. Install ShaydZ
```bash
# Clone repository
git clone https://github.com/shaydz93/shaydz-super-monitor.git
cd shaydz-super-monitor

# Run production installer
chmod +x install.sh
./install.sh
```

### 3. Post-Installation Configuration

#### Firewall Configuration
```bash
# Check firewall status
sudo ufw status

# Allow specific IPs only (optional)
sudo ufw allow from 192.168.1.0/24 to any port 5001
```

#### SSL/TLS Setup (Optional)
```bash
# Install certbot for Let's Encrypt
sudo apt install certbot

# Set up reverse proxy with nginx
sudo nano /etc/nginx/sites-available/shaydz
```

#### Performance Tuning
```bash
# Optimize for Raspberry Pi
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf

# GPU memory split (for headless Pi)
echo 'gpu_mem=16' | sudo tee -a /boot/config.txt
```

## Production Configuration

### 1. Environment Variables
Create `/opt/shaydz/.env`:
```bash
FLASK_DEBUG=false
SHAYDZ_ENV=production
SESSION_TIMEOUT=3600
MAX_FAILED_LOGINS=5
ENABLE_AI=true
```

### 2. Database Configuration
```bash
# Set proper permissions
chmod 600 /opt/shaydz/*.json
chown shaydz:shaydz /opt/shaydz/*.json
```

### 3. Log Management
```bash
# Configure log rotation
sudo systemctl enable logrotate
sudo systemctl start logrotate

# Check log size
du -sh /opt/shaydz/shaydz.log
```

## Monitoring & Maintenance

### Health Checks
```bash
# Run health check
./health_check.sh

# Check service status
sudo systemctl status shaydz

# View logs
sudo journalctl -u shaydz -f
```

### Automated Monitoring
```bash
# Add to crontab for automated health checks
echo "0 */6 * * * /opt/shaydz/health_check.sh >> /var/log/shaydz-health.log 2>&1" | crontab -
```

### Updates
```bash
# Update ShaydZ
cd /opt/shaydz
git pull origin main
sudo systemctl restart shaydz
```

## Security Hardening

### 1. System Hardening
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Configure SSH properly
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PermitRootLogin no
```

### 2. Network Security
```bash
# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Check banned IPs
sudo fail2ban-client status shaydz
```

### 3. Application Security
```bash
# Set secure file permissions
chmod 700 /opt/shaydz
chmod 600 /opt/shaydz/.api_key
chmod 600 /opt/shaydz/admin_user.json
```

## Backup Strategy

### Configuration Backup
```bash
#!/bin/bash
# Backup script
BACKUP_DIR="/home/shaydz/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/shaydz_backup_$DATE.tar.gz \
    /opt/shaydz/*.json \
    /opt/shaydz/.api_key \
    /opt/shaydz/shaydz.log \
    /etc/systemd/system/shaydz.service
```

### Automated Backups
```bash
# Add to crontab
echo "0 2 * * * /home/shaydz/backup_shaydz.sh" | crontab -
```

## Troubleshooting

### Common Issues

**Service Won't Start**
```bash
# Check service logs
sudo journalctl -u shaydz -n 50

# Check permissions
ls -la /opt/shaydz/

# Test manually
cd /opt/shaydz
source venv/bin/activate
python3 shaydz.py
```

**Web UI Not Accessible**
```bash
# Check if port is open
sudo netstat -tlnp | grep 5001

# Check firewall
sudo ufw status
```

**High CPU Usage**
```bash
# Check AI settings
cat /opt/shaydz/ai_config.json

# Monitor system resources
htop
```

### Performance Optimization

**Memory Usage**
```bash
# Adjust Python memory settings
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

**Disk I/O**
```bash
# Move logs to RAM disk (optional)
sudo mkdir /mnt/ramdisk
echo "tmpfs /mnt/ramdisk tmpfs defaults,size=100M 0 0" | sudo tee -a /etc/fstab
```

## Scaling & High Availability

### Multiple Instances
```bash
# Run multiple instances on different ports
cp /etc/systemd/system/shaydz.service /etc/systemd/system/shaydz-backup.service
# Edit port and working directory
```

### Load Balancing
```bash
# Configure nginx upstream
upstream shaydz {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002 backup;
}
```

## Compliance & Auditing

### Security Audit
```bash
# Run security audit
sudo lynis audit system

# Check open ports
sudo nmap -sS -O localhost
```

### Log Analysis
```bash
# Analyze access patterns
grep "LOGIN" /opt/shaydz/shaydz.log | tail -100

# Check for anomalies
grep "ANOMALY" /opt/shaydz/shaydz.log | tail -50
```

## Production Checklist

Before going live:
- [ ] All tests pass
- [ ] Health check passes
- [ ] Firewall configured
- [ ] Fail2ban enabled
- [ ] Logs rotating properly
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] SSL/TLS configured (if required)
- [ ] Performance optimized
- [ ] Security hardened
- [ ] Documentation updated
- [ ] Team trained on operations

## Emergency Procedures

### Quick Recovery
```bash
# Stop service
sudo systemctl stop shaydz

# Restore from backup
tar -xzf /home/shaydz/backups/shaydz_backup_latest.tar.gz -C /

# Restart service
sudo systemctl start shaydz
```

### Factory Reset
```bash
# Stop service
sudo systemctl stop shaydz

# Remove all data
rm -f /opt/shaydz/*.json
rm -f /opt/shaydz/.api_key
rm -f /opt/shaydz/shaydz.log

# Restart service (will recreate defaults)
sudo systemctl start shaydz
```

---

**This guide ensures a secure, scalable, and maintainable production deployment of ShaydZ Super Monitor.**
