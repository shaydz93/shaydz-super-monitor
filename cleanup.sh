#!/bin/bash
# S h a y d Z Super Monitor - Repository Cleanup Script
# This script cleans up generated files and prepares the repo for commit

echo "🧹 Cleaning up S h a y d Z Super Monitor repository..."

# Remove Python cache files
echo "  Removing Python cache files..."
rm -rf __pycache__/
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Remove generated configuration files
echo "  Removing generated config files..."
rm -f ai_config.json
rm -f ai_learning.json
rm -f baseline.json
rm -f admin_user.json
rm -f .api_key

# Remove log files
echo "  Removing log files..."
rm -f *.log
rm -f *.log.*

# Remove temporary files
echo "  Removing temporary files..."
rm -f *.tmp
rm -f *.bak
rm -f *.orig
rm -f *~

# Remove IDE files
echo "  Removing IDE files..."
rm -rf .vscode/
rm -rf .idea/
rm -f *.sublime-*

# Remove system files
echo "  Removing system files..."
rm -f .DS_Store
rm -f Thumbs.db
rm -f *.swp
rm -f *.swo

echo "✅ Repository cleanup complete!"
echo "📦 Ready for commit and push!"
