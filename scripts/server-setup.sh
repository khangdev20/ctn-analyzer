#!/bin/bash

# Server Setup Script for Trending Intelligence System
# Run this script on your Linux server (Ubuntu/Debian) to set up the environment

set -e

echo "🚀 Setting up Trending Intelligence System on Linux Server"
echo "============================================================"

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    curl \
    htop \
    ufw \
    certbot \
    python3-certbot-nginx

# Create application user
echo "👤 Creating application user..."
sudo useradd -m -s /bin/bash trending || echo "User already exists"
sudo usermod -aG sudo trending

# Create application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/trending-intelligence
sudo chown trending:trending /opt/trending-intelligence

# Clone repository (you'll need to update this with your repo URL)
echo "📥 Cloning repository..."
cd /opt/trending-intelligence
sudo -u trending git clone https://github.com/khangdev20/cnt-analyzer.git .
sudo -u trending git checkout develop

# Set up Python virtual environment
echo "🐍 Setting up Python environment..."
sudo -u trending python3 -m venv /opt/trending-intelligence/venv
sudo -u trending /opt/trending-intelligence/venv/bin/pip install --upgrade pip
sudo -u trending /opt/trending-intelligence/venv/bin/pip install -r requirements.txt

# Create required directories
echo "📂 Creating required directories..."
sudo -u trending mkdir -p /opt/trending-intelligence/{data/{raw,processed,reports},logs,config}

# Set up environment file
echo "⚙️ Setting up environment configuration..."
sudo -u trending tee /opt/trending-intelligence/.env > /dev/null << 'EOF'
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# API Keys (update these with your actual keys)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GEMINI_API_KEY=your-gemini-key

# Discord Configuration
DISCORD_WEBHOOK=your-discord-webhook-url

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Server Configuration
HOST=0.0.0.0
PORT=5000
EOF

echo "⚠️  IMPORTANT: Update /opt/trending-intelligence/.env with your actual API keys!"

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/trending-intelligence.service > /dev/null << 'EOF'
[Unit]
Description=Trending Intelligence System
After=network.target

[Service]
Type=simple
User=trending
Group=trending
WorkingDirectory=/opt/trending-intelligence
Environment=PATH=/opt/trending-intelligence/venv/bin
ExecStart=/opt/trending-intelligence/venv/bin/python run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Environment file
EnvironmentFile=/opt/trending-intelligence/.env

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx reverse proxy
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/trending-intelligence > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Update with your domain

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
    
    # Static files (if any)
    location /static {
        alias /opt/trending-intelligence/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/trending-intelligence /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable trending-intelligence
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl start trending-intelligence

# Check service status
echo "📊 Checking service status..."
sudo systemctl status trending-intelligence --no-pager -l
sudo systemctl status nginx --no-pager -l

# Set up log rotation
echo "📄 Setting up log rotation..."
sudo tee /etc/logrotate.d/trending-intelligence > /dev/null << 'EOF'
/opt/trending-intelligence/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
    su trending trending
}
EOF

# Create health check script
echo "🏥 Creating health check script..."
sudo -u trending tee /opt/trending-intelligence/health-check.sh > /dev/null << 'EOF'
#!/bin/bash

# Health check script for monitoring
HEALTH_URL="http://localhost:5000/health"
LOG_FILE="/opt/trending-intelligence/logs/health-check.log"

if curl -f -s "$HEALTH_URL" > /dev/null; then
    echo "$(date): ✅ Health check passed" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): ❌ Health check failed" >> "$LOG_FILE"
    # Restart service if health check fails
    sudo systemctl restart trending-intelligence
    exit 1
fi
EOF

sudo chmod +x /opt/trending-intelligence/health-check.sh

# Set up cron job for health checks
echo "⏰ Setting up health check cron job..."
(sudo -u trending crontab -l 2>/dev/null; echo "*/5 * * * * /opt/trending-intelligence/health-check.sh") | sudo -u trending crontab -

echo ""
echo "✅ Server setup completed successfully!"
echo "============================================================"
echo "📋 Next Steps:"
echo "1. Update /opt/trending-intelligence/.env with your API keys"
echo "2. Update domain in /etc/nginx/sites-available/trending-intelligence"
echo "3. Set up SSL certificate:"
echo "   sudo certbot --nginx -d your-domain.com"
echo "4. Test the deployment:"
echo "   curl http://localhost:5000/health"
echo "5. Monitor logs:"
echo "   sudo journalctl -u trending-intelligence -f"
echo ""
echo "🎉 Your Trending Intelligence System is ready!"
echo "Access it at: http://your-server-ip or http://your-domain.com"