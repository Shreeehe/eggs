#!/bin/bash
# Raspberry Pi Egg Price Automation Setup Script
# Run this script to set up the complete automation system

echo "🥚 Setting up Egg Price Automation on Raspberry Pi..."

# Create project directory
PROJECT_DIR="$HOME/egg-price-automation"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "📁 Created project directory: $PROJECT_DIR"

# Install required Python packages
echo "📦 Installing Python dependencies..."
pip3 install --user requests pandas beautifulsoup4 streamlit plotly

# Create data directory
mkdir -p egg_data
echo "📂 Created data directory"

# Create Python scripts (you'll need to save the Python files here)
echo "📝 Python scripts should be saved as:"
echo "  - egg_scraper.py (main scraper)"
echo "  - dashboard.py (Streamlit dashboard)"

# Make scripts executable
chmod +x egg_scraper.py 2>/dev/null || echo "⚠️  egg_scraper.py not found - please create it first"

# Setup cron job for daily 10 AM execution
echo "⏰ Setting up daily cron job..."

CRON_JOB="0 10 * * * cd $PROJECT_DIR && /usr/bin/python3 egg_scraper.py >> egg_scraper.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -F "$PROJECT_DIR/egg_scraper.py") || {
    echo "Adding cron job..."
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job added - will run daily at 10:00 AM"
}

# Create systemd service for Streamlit (auto-start on boot)
echo "🖥️  Setting up Streamlit service..."

SERVICE_FILE="/etc/systemd/system/egg-dashboard.service"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Egg Price Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 -m streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable egg-dashboard.service

echo "🎯 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Save the Python scripts in: $PROJECT_DIR"
echo "   - egg_scraper.py (scraper code)"
echo "   - dashboard.py (Streamlit dashboard code)"
echo ""
echo "2. Test the scraper manually:"
echo "   cd $PROJECT_DIR && python3 egg_scraper.py"
echo ""
echo "3. Start the dashboard:"
echo "   sudo systemctl start egg-dashboard.service"
echo ""
echo "4. Access dashboard at: http://your-pi-ip:8501"
echo ""
echo "📊 Cron job schedule: Daily at 10:00 AM"
echo "🔄 Dashboard: Auto-starts on boot"
echo ""
echo "📝 Logs:"
echo "  - Scraper: $PROJECT_DIR/egg_scraper.log"
echo "  - Dashboard: sudo journalctl -u egg-dashboard.service"
echo ""
echo "🔧 Useful commands:"
echo "  - View cron jobs: crontab -l"
echo "  - Check dashboard status: sudo systemctl status egg-dashboard"
echo "  - Restart dashboard: sudo systemctl restart egg-dashboard"