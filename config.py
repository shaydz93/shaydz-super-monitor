"""
Production Configuration for S h a y d Z Super Monitor
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
BASELINE_FILE = os.path.join(BASE_DIR, "baseline.json")
ADMIN_FILE = os.path.join(BASE_DIR, "admin_user.json")
API_KEY_FILE = os.path.join(BASE_DIR, ".api_key")
LOG_FILE = os.path.join(BASE_DIR, "shaydz.log")

# Monitoring settings
MIN_HISTORY = 20
MONITORED_HOSTS = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]  # Google, Cloudflare, OpenDNS
ANOMALY_THRESHOLD = 3  # Standard deviations
UPDATE_INTERVAL = 5  # seconds
THREAT_INTEL_INTERVAL = 1800  # seconds (30 minutes)

# Web UI settings
WEB_HOST = "0.0.0.0"
WEB_PORT = 5001
WEB_DEBUG = False  # Always False for production

# Display settings
EPD_WIDTH = 122
EPD_HEIGHT = 250
FONT_SIZE = 14

# Production logging configuration
def setup_logging():
    """Configure production-grade logging"""
    logger = logging.getLogger('shaydz')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (only for WARNING and above in production)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger

# Temperature thresholds
TEMP_CRITICAL = 80.0  # Celsius
TEMP_WARNING = 70.0   # Celsius

# Security settings
MAX_FAILED_LOGINS = 10
IPTABLES_BLOCK_THREATS = True
SESSION_TIMEOUT = 3600  # 1 hour

# AI settings
AI_PATTERN_WINDOW = 1000  # Maximum patterns to store
AI_LEARNING_THRESHOLD = 50  # Minimum patterns before learning
AI_CONFIDENCE_THRESHOLD = 0.8
AI_MAX_RETRIES = 3
AI_TIMEOUT = 30  # seconds

# Performance settings
MAX_CONCURRENT_TASKS = 5
MEMORY_LIMIT_MB = 512
CPU_LIMIT_PERCENT = 80

# Error handling
ENABLE_ERROR_REPORTING = True
MAX_ERROR_REPORTS = 100
