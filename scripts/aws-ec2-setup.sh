#!/bin/bash

# AWS EC2 Deployment Script
# Run this after setting up your EC2 instance

set -e

echo "🚀 AWS EC2 Deployment for Trending Intelligence System"
echo "======================================================"

# Install AWS CLI if not present
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Install CloudWatch agent
echo "📊 Installing CloudWatch agent..."
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
echo "⚙️ Configuring CloudWatch monitoring..."
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json > /dev/null << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "cwagent"
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/trending-intelligence/logs/*.log",
                        "log_group_name": "trending-intelligence-app",
                        "log_stream_name": "{instance_id}/app",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/nginx/access.log",
                        "log_group_name": "trending-intelligence-nginx",
                        "log_stream_name": "{instance_id}/access",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/nginx/error.log",
                        "log_group_name": "trending-intelligence-nginx",
                        "log_stream_name": "{instance_id}/error",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "TrendingIntelligence",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Set up automatic security updates
echo "🔒 Configuring automatic security updates..."
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Create backup script
echo "💾 Setting up automated backups..."
sudo tee /opt/trending-intelligence/backup.sh > /dev/null << 'EOF'
#!/bin/bash

# Backup script for Trending Intelligence System
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/trending-backup-$DATE"
S3_BUCKET="your-backup-bucket"  # Update with your S3 bucket

echo "📦 Creating backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup application data
cp -r /opt/trending-intelligence/data "$BACKUP_DIR/"
cp -r /opt/trending-intelligence/logs "$BACKUP_DIR/"
cp /opt/trending-intelligence/.env "$BACKUP_DIR/"

# Create tarball
tar -czf "/tmp/trending-backup-$DATE.tar.gz" -C "/tmp" "trending-backup-$DATE"

# Upload to S3
aws s3 cp "/tmp/trending-backup-$DATE.tar.gz" "s3://$S3_BUCKET/backups/"

# Cleanup local backup
rm -rf "$BACKUP_DIR" "/tmp/trending-backup-$DATE.tar.gz"

echo "✅ Backup completed: s3://$S3_BUCKET/backups/trending-backup-$DATE.tar.gz"
EOF

chmod +x /opt/trending-intelligence/backup.sh

# Set up daily backups
(sudo -u trending crontab -l 2>/dev/null; echo "0 2 * * * /opt/trending-intelligence/backup.sh") | sudo -u trending crontab -

# Configure instance metadata
echo "📋 Configuring instance metadata..."
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region)

echo "🏷️ Instance ID: $INSTANCE_ID"
echo "🌍 Region: $REGION"

# Add tags to instance (requires AWS CLI configured with appropriate permissions)
echo "🏷️ Adding instance tags..."
aws ec2 create-tags --region "$REGION" --resources "$INSTANCE_ID" --tags \
    Key=Name,Value=trending-intelligence \
    Key=Environment,Value=production \
    Key=Application,Value=trending-intelligence-system \
    Key=AutoBackup,Value=true \
    || echo "Note: Failed to add tags (may need additional IAM permissions)"

echo ""
echo "✅ AWS EC2 deployment configuration completed!"
echo "=============================================="
echo "📋 AWS-specific features configured:"
echo "• CloudWatch monitoring and logging"
echo "• Automated security updates"
echo "• Daily S3 backups (update S3_BUCKET in backup.sh)"
echo "• Instance tagging"
echo ""
echo "🔧 Additional AWS setup needed:"
echo "1. Configure IAM role for EC2 instance with:"
echo "   - CloudWatchAgentServerPolicy"
echo "   - S3 backup bucket access"
echo "2. Create S3 bucket for backups"
echo "3. Configure security groups:"
echo "   - Allow HTTP (80) and HTTPS (443)"
echo "   - Allow SSH (22) from your IP only"
echo "4. Set up Application Load Balancer (optional)"
echo "5. Configure Route 53 DNS (optional)"