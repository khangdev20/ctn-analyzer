#!/bin/bash

# Google Cloud Platform Deployment Script
# Run this after setting up your GCP Compute Engine instance

set -e

echo "🚀 GCP Compute Engine Deployment for Trending Intelligence System"
echo "================================================================="

# Install Google Cloud SDK if not present
if ! command -v gcloud &> /dev/null; then
    echo "📦 Installing Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    gcloud init
fi

# Install Cloud Ops Agent (replaces both Monitoring and Logging agents)
echo "📊 Installing Cloud Ops Agent..."
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
rm add-google-cloud-ops-agent-repo.sh

# Configure Cloud Ops Agent
echo "⚙️ Configuring Cloud Monitoring and Logging..."
sudo tee /etc/google-cloud-ops-agent/config.yaml > /dev/null << 'EOF'
logging:
  receivers:
    trending_intelligence_app:
      type: files
      include_paths:
        - /opt/trending-intelligence/logs/*.log
    trending_intelligence_nginx_access:
      type: files
      include_paths:
        - /var/log/nginx/access.log
    trending_intelligence_nginx_error:
      type: files
      include_paths:
        - /var/log/nginx/error.log
    trending_intelligence_systemd:
      type: systemd_journald
      include_units:
        - trending-intelligence.service
  
  processors:
    trending_intelligence_parser:
      type: regex_parser
      field: message
      regex: '^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (?P<level>\w+) - (?P<message>.*)$'
      time_key: timestamp
      time_format: '%Y-%m-%d %H:%M:%S'
  
  service:
    pipelines:
      default_pipeline:
        receivers:
          - trending_intelligence_app
          - trending_intelligence_nginx_access
          - trending_intelligence_nginx_error
          - trending_intelligence_systemd
        processors:
          - trending_intelligence_parser

metrics:
  receivers:
    hostmetrics:
      type: hostmetrics
      collection_interval: 60s
  
  processors:
    metrics_filter:
      type: exclude_metrics
      metrics_pattern:
        - system.cpu.utilization
        - system.memory.utilization
        - system.disk.io_time
  
  service:
    pipelines:
      default_pipeline:
        receivers:
          - hostmetrics
        processors:
          - metrics_filter
EOF

# Restart Cloud Ops Agent
sudo systemctl restart google-cloud-ops-agent

# Set up automatic OS updates
echo "🔒 Configuring automatic OS updates..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Create backup script for Google Cloud Storage
echo "💾 Setting up automated backups to Google Cloud Storage..."
sudo tee /opt/trending-intelligence/gcs-backup.sh > /dev/null << 'EOF'
#!/bin/bash

# Backup script for Google Cloud Storage
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/trending-backup-$DATE"
GCS_BUCKET="your-backup-bucket"  # Update with your GCS bucket

echo "📦 Creating backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application data
cp -r /opt/trending-intelligence/data "$BACKUP_DIR/"
cp -r /opt/trending-intelligence/logs "$BACKUP_DIR/"
cp /opt/trending-intelligence/.env "$BACKUP_DIR/"

# Create tarball
tar -czf "/tmp/trending-backup-$DATE.tar.gz" -C "/tmp" "trending-backup-$DATE"

# Upload to Google Cloud Storage
gsutil cp "/tmp/trending-backup-$DATE.tar.gz" "gs://$GCS_BUCKET/backups/"

# Cleanup local backup
rm -rf "$BACKUP_DIR" "/tmp/trending-backup-$DATE.tar.gz"

echo "✅ Backup completed: gs://$GCS_BUCKET/backups/trending-backup-$DATE.tar.gz"
EOF

chmod +x /opt/trending-intelligence/gcs-backup.sh

# Set up daily backups
(sudo -u trending crontab -l 2>/dev/null; echo "0 2 * * * /opt/trending-intelligence/gcs-backup.sh") | sudo -u trending crontab -

# Get instance metadata
echo "📋 Configuring instance metadata..."
INSTANCE_NAME=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/name)
ZONE=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone | cut -d'/' -f4)
PROJECT_ID=$(curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/project-id)

echo "🏷️ Instance Name: $INSTANCE_NAME"
echo "🌍 Zone: $ZONE"
echo "📝 Project ID: $PROJECT_ID"

# Add labels to instance
echo "🏷️ Adding instance labels..."
gcloud compute instances add-labels "$INSTANCE_NAME" \
    --zone="$ZONE" \
    --labels=environment=production,application=trending-intelligence,auto-backup=true \
    || echo "Note: Failed to add labels (may need additional permissions)"

# Set up health check for load balancer
echo "🏥 Creating health check endpoint configuration..."
sudo tee /etc/nginx/sites-available/health-check > /dev/null << 'EOF'
server {
    listen 8080;
    server_name _;
    
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    location / {
        return 404;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/health-check /etc/nginx/sites-enabled/health-check
sudo nginx -t && sudo systemctl reload nginx

# Configure firewall rules (using ufw, but GCP firewall rules should also be set)
echo "🔒 Configuring firewall..."
sudo ufw allow 8080/tcp comment 'Health check port'

# Create startup script for auto-deployment
echo "🚀 Creating startup script for auto-deployment..."
sudo tee /opt/trending-intelligence/startup.sh > /dev/null << 'EOF'
#!/bin/bash

# Startup script for GCP instance
LOG_FILE="/opt/trending-intelligence/logs/startup.log"

echo "$(date): 🚀 Instance startup initiated" >> "$LOG_FILE"

# Wait for network
sleep 30

# Update application if auto-deploy is enabled
if [ -f "/opt/trending-intelligence/.auto-deploy" ]; then
    echo "$(date): 📥 Auto-deploy enabled, updating application..." >> "$LOG_FILE"
    cd /opt/trending-intelligence
    sudo -u trending git pull origin main >> "$LOG_FILE" 2>&1
    sudo -u trending /opt/trending-intelligence/venv/bin/pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    sudo systemctl restart trending-intelligence
fi

echo "$(date): ✅ Startup script completed" >> "$LOG_FILE"
EOF

chmod +x /opt/trending-intelligence/startup.sh

# Add startup script to systemd
sudo tee /etc/systemd/system/trending-startup.service > /dev/null << 'EOF'
[Unit]
Description=Trending Intelligence Startup Script
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/trending-intelligence/startup.sh
User=root
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable trending-startup.service

echo ""
echo "✅ GCP Compute Engine deployment configuration completed!"
echo "========================================================"
echo "📋 GCP-specific features configured:"
echo "• Cloud Ops Agent (Monitoring + Logging)"
echo "• Automated OS updates"
echo "• Daily GCS backups (update GCS_BUCKET in gcs-backup.sh)"
echo "• Instance labeling"
echo "• Health check endpoint on port 8080"
echo "• Auto-deployment startup script"
echo ""
echo "🔧 Additional GCP setup needed:"
echo "1. Create GCS bucket for backups:"
echo "   gsutil mb gs://your-backup-bucket"
echo "2. Configure firewall rules:"
echo "   gcloud compute firewall-rules create allow-http --allow tcp:80"
echo "   gcloud compute firewall-rules create allow-https --allow tcp:443"
echo "   gcloud compute firewall-rules create allow-health-check --allow tcp:8080"
echo "3. Set up HTTP(S) Load Balancer (optional)"
echo "4. Configure Cloud DNS (optional)"
echo "5. Set up SSL certificate with Google-managed certificates"
echo "6. Configure IAM roles for service account (if using)"