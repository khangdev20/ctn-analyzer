# Deployment Guide for Trending Intelligence System

This guide provides step-by-step instructions for deploying the Trending Intelligence System using GitHub Actions CI/CD with AWS EC2 or Google Cloud Platform.

## 🚀 Quick Start

### Prerequisites

- GitHub repository with your code
- AWS Account (for EC2) or Google Cloud Account (for GCP)
- Domain name (optional but recommended)
- API keys for OpenAI, Anthropic, and Gemini
- Discord webhook URL

### 1. GitHub Secrets Configuration

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add the following secrets:

#### Required for all deployments:

```
SSH_PRIVATE_KEY=<your-ssh-private-key>
SERVER_USER=trending
SSH_PORT=22
```

#### For staging environment:

```
STAGING_HOST=<your-staging-server-ip>
```

#### For production environment:

```
PRODUCTION_HOST=<your-production-server-ip>
```

#### For AWS EC2 deployment (optional):

```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_REGION=us-east-1
```

#### For GCP deployment (optional):

```
GCP_SA_KEY=<your-service-account-json>
GCP_ZONE=us-central1-a
```

### 2. Server Setup

#### Option A: Manual Server Setup (Recommended for first deployment)

1. **Provision a Linux server** (Ubuntu 20.04+ or Debian 11+)

   - Minimum: 2 vCPU, 4GB RAM, 20GB storage
   - Recommended: 4 vCPU, 8GB RAM, 40GB storage

2. **Run the setup script**:

   ```bash
   wget https://raw.githubusercontent.com/yourusername/cnt-analyzer/main/scripts/server-setup.sh
   chmod +x server-setup.sh
   sudo ./server-setup.sh
   ```

3. **Configure your environment**:

   ```bash
   sudo nano /opt/trending-intelligence/.env
   ```

   Update with your actual API keys and Discord webhook.

4. **Update domain configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/trending-intelligence
   ```
   Replace `your-domain.com` with your actual domain.

#### Option B: AWS EC2 Setup

1. **Launch EC2 instance**:

   - AMI: Ubuntu Server 20.04 LTS
   - Instance type: t3.medium or larger
   - Security groups: Allow HTTP (80), HTTPS (443), SSH (22)
   - Tag: Name=trending-intelligence

2. **Run setup scripts**:

   ```bash
   # Basic setup
   wget https://raw.githubusercontent.com/yourusername/cnt-analyzer/main/scripts/server-setup.sh
   chmod +x server-setup.sh
   sudo ./server-setup.sh

   # AWS-specific configuration
   wget https://raw.githubusercontent.com/yourusername/cnt-analyzer/main/scripts/aws-ec2-setup.sh
   chmod +x aws-ec2-setup.sh
   sudo ./aws-ec2-setup.sh
   ```

3. **Configure IAM role** for the EC2 instance with:
   - CloudWatchAgentServerPolicy
   - S3 backup bucket access

#### Option C: Google Cloud Platform Setup

1. **Create Compute Engine instance**:

   - Machine type: e2-medium or larger
   - Boot disk: Ubuntu 20.04 LTS
   - Firewall: Allow HTTP and HTTPS traffic
   - Labels: environment=production, application=trending-intelligence

2. **Run setup scripts**:

   ```bash
   # Basic setup
   wget https://raw.githubusercontent.com/yourusername/cnt-analyzer/main/scripts/server-setup.sh
   chmod +x server-setup.sh
   sudo ./server-setup.sh

   # GCP-specific configuration
   wget https://raw.githubusercontent.com/yourusername/cnt-analyzer/main/scripts/gcp-setup.sh
   chmod +x gcp-setup.sh
   sudo ./gcp-setup.sh
   ```

### 3. SSL Certificate Setup

After DNS is configured and pointing to your server:

```bash
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

### 4. Testing the Deployment

1. **Health check**:

   ```bash
   curl http://your-domain.com/health
   ```

2. **Service status**:

   ```bash
   sudo systemctl status trending-intelligence
   sudo systemctl status nginx
   ```

3. **View logs**:
   ```bash
   sudo journalctl -u trending-intelligence -f
   tail -f /opt/trending-intelligence/logs/bot.log
   ```

## 🔄 CI/CD Workflow

### Deployment Triggers

- **Staging**: Push to `develop` branch
- **Production**: Push to `main` branch
- **AWS EC2**: Push to `main` with `[deploy-aws]` in commit message
- **GCP**: Push to `main` with `[deploy-gcp]` in commit message

### Example Deployment Commands

```bash
# Deploy to staging
git push origin develop

# Deploy to production
git push origin main

# Deploy to AWS EC2
git commit -m "feat: new feature [deploy-aws]"
git push origin main

# Deploy to GCP
git commit -m "feat: new feature [deploy-gcp]"
git push origin main
```

## 📊 Monitoring and Maintenance

### System Monitoring

1. **Application health**: http://your-domain.com/health
2. **System status**: http://your-domain.com/status
3. **Metrics**: http://your-domain.com/metrics

### Log Locations

- Application logs: `/opt/trending-intelligence/logs/`
- System logs: `sudo journalctl -u trending-intelligence`
- Nginx logs: `/var/log/nginx/`
- Health check logs: `/opt/trending-intelligence/logs/health-check.log`

### Backup and Recovery

#### AWS S3 Backups

- Automated daily backups to S3
- Backup script: `/opt/trending-intelligence/backup.sh`
- Restore: Download from S3 and extract to `/opt/trending-intelligence/`

#### GCP Cloud Storage Backups

- Automated daily backups to GCS
- Backup script: `/opt/trending-intelligence/gcs-backup.sh`
- Restore: `gsutil cp gs://bucket/backup.tar.gz ./ && tar -xzf backup.tar.gz`

### Scaling Considerations

#### Horizontal Scaling

- Use load balancer (ALB on AWS, HTTP(S) LB on GCP)
- Deploy multiple instances
- Use external database (RDS, Cloud SQL)
- Use external cache (ElastiCache, Memorystore)

#### Vertical Scaling

- Increase instance size
- Add more storage
- Optimize Python processes

## 🛠️ Troubleshooting

### Common Issues

1. **Service won't start**:

   ```bash
   sudo journalctl -u trending-intelligence -n 50
   sudo systemctl status trending-intelligence
   ```

2. **API keys not working**:

   ```bash
   sudo nano /opt/trending-intelligence/.env
   sudo systemctl restart trending-intelligence
   ```

3. **Nginx configuration**:

   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Disk space issues**:

   ```bash
   df -h
   sudo journalctl --vacuum-time=7d
   ```

5. **High memory usage**:
   ```bash
   htop
   sudo systemctl restart trending-intelligence
   ```

### Emergency Recovery

1. **Rollback deployment**:

   ```bash
   cd /opt/trending-intelligence
   git checkout HEAD~1
   sudo systemctl restart trending-intelligence
   ```

2. **Restore from backup**:

   ```bash
   # AWS
   aws s3 cp s3://backup-bucket/latest-backup.tar.gz ./
   tar -xzf latest-backup.tar.gz
   sudo systemctl restart trending-intelligence

   # GCP
   gsutil cp gs://backup-bucket/latest-backup.tar.gz ./
   tar -xzf latest-backup.tar.gz
   sudo systemctl restart trending-intelligence
   ```

## 📈 Performance Optimization

### System Optimization

- Enable gzip compression in Nginx
- Use HTTP/2
- Implement caching strategies
- Optimize Python application (async/await, connection pooling)
- Use CDN for static assets

### Database Optimization

- Use indexed queries
- Implement connection pooling
- Regular cleanup of old data
- Consider read replicas for heavy read workloads

### Monitoring Setup

- AWS: CloudWatch dashboards and alarms
- GCP: Cloud Monitoring dashboards and alerts
- Application Performance Monitoring (APM) tools
- Log aggregation and analysis

## 🔒 Security Best Practices

### Server Security

- Regular OS updates (automated via unattended-upgrades)
- Firewall configuration (ufw + cloud provider security groups)
- SSH key-based authentication only
- Regular security patches
- Intrusion detection systems

### Application Security

- Environment variable protection
- API key rotation
- HTTPS enforcement
- Rate limiting
- Input validation
- Regular dependency updates

### Network Security

- VPC/VPN setup
- Private subnets for databases
- WAF (Web Application Firewall)
- DDoS protection
- SSL/TLS certificate management

## 📞 Support

For issues with deployment or configuration:

1. Check the troubleshooting section above
2. Review application and system logs
3. Verify all environment variables are set correctly
4. Ensure all required services are running
5. Check network connectivity and firewall rules

The deployment is designed to be robust and self-healing with automatic restarts, health checks, and monitoring in place.
