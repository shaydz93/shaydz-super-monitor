# Production Health Check Script
#!/bin/bash

# S h a y d Z Super Monitor Health Check
# Run this script to verify all components are working correctly

echo "=== S h a y d Z Super Monitor Health Check ==="
echo "$(date)"
echo

# Check if service is running
echo "1. Checking systemd service status..."
if systemctl is-active --quiet shaydz; then
    echo "   ✓ ShaydZ service is running"
else
    echo "   ✗ ShaydZ service is not running"
    echo "   Try: sudo systemctl start shaydz"
fi

# Check if web UI is accessible
echo "2. Checking web UI accessibility..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001 | grep -q "200"; then
    echo "   ✓ Web UI is accessible"
else
    echo "   ✗ Web UI is not accessible"
    echo "   Check firewall and service status"
fi

# Check log files
echo "3. Checking log files..."
if [ -f "/opt/shaydz/shaydz.log" ]; then
    echo "   ✓ Log file exists"
    ERROR_COUNT=$(grep -c "ERROR" /opt/shaydz/shaydz.log 2>/dev/null || echo "0")
    echo "   📊 Recent errors: $ERROR_COUNT"
else
    echo "   ✗ Log file not found"
fi

# Check disk space
echo "4. Checking disk space..."
DISK_USAGE=$(df /opt/shaydz | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "   ✓ Disk space OK ($DISK_USAGE% used)"
else
    echo "   ⚠ Disk space low ($DISK_USAGE% used)"
fi

# Check memory usage
echo "5. Checking memory usage..."
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEMORY_USAGE" -lt 80 ]; then
    echo "   ✓ Memory usage OK ($MEMORY_USAGE% used)"
else
    echo "   ⚠ Memory usage high ($MEMORY_USAGE% used)"
fi

# Check network connectivity
echo "6. Checking network connectivity..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "   ✓ Internet connectivity OK"
else
    echo "   ✗ No internet connectivity"
fi

# Check AI configuration
echo "7. Checking AI configuration..."
if [ -f "/opt/shaydz/ai_config.json" ]; then
    echo "   ✓ AI configuration exists"
    AI_ENABLED=$(python3 -c "import json; print(json.load(open('/opt/shaydz/ai_config.json')).get('ai_enabled', False))" 2>/dev/null || echo "False")
    echo "   📊 AI enabled: $AI_ENABLED"
else
    echo "   ℹ AI configuration not found (will use defaults)"
fi

# Check threat intelligence
echo "8. Checking threat intelligence..."
if [ -f "/opt/shaydz/baseline.json" ]; then
    echo "   ✓ Baseline data exists"
else
    echo "   ℹ Baseline data not found (system is learning)"
fi

# Check fail2ban
echo "9. Checking security..."
if systemctl is-active --quiet fail2ban; then
    echo "   ✓ Fail2ban is running"
    BANNED_IPS=$(sudo fail2ban-client status shaydz 2>/dev/null | grep "Banned IP list" | wc -l || echo "0")
    echo "   📊 Banned IPs: $BANNED_IPS"
else
    echo "   ⚠ Fail2ban is not running"
fi

# Check firewall
echo "10. Checking firewall..."
if sudo ufw status | grep -q "Status: active"; then
    echo "   ✓ UFW firewall is active"
else
    echo "   ⚠ UFW firewall is not active"
fi

echo
echo "=== Health Check Complete ==="
echo "For detailed logs: sudo journalctl -u shaydz -f"
echo "Service control: sudo systemctl {start|stop|restart|status} shaydz"
