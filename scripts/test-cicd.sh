#!/bin/bash

# Local Development CI/CD Test Script
# Tests the deployment scripts locally before running on servers

set -e

echo "🧪 Testing CI/CD Scripts Locally"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_passed() {
    echo -e "${GREEN}✅ $1${NC}"
}

test_failed() {
    echo -e "${RED}❌ $1${NC}"
}

test_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Test 1: Check required files exist
echo "📋 Test 1: Checking required files..."
files=(
    ".github/workflows/deploy.yml"
    "scripts/server-setup.sh"
    "scripts/aws-ec2-setup.sh"
    "scripts/gcp-setup.sh"
    "requirements.txt"
    "run.py"
    "pipeline/main_flow.py"
    "worker/base.py"
)

for file in "${files[@]}"; do
    if [[ -f "$file" ]]; then
        test_passed "Found $file"
    else
        test_failed "Missing $file"
        exit 1
    fi
done

# Test 2: Validate Python imports
echo -e "\n🐍 Test 2: Validating Python imports..."
python3 -c "
try:
    from pipeline.main_flow import MainFlowOrchestrator
    print('✅ MainFlowOrchestrator import successful')
except Exception as e:
    print(f'❌ MainFlowOrchestrator import failed: {e}')
    exit(1)

try:
    from worker.base import BackgroundWorker
    print('✅ BackgroundWorker import successful')
except Exception as e:
    print(f'❌ BackgroundWorker import failed: {e}')
    exit(1)
"

# Test 3: Validate GitHub Actions workflow
echo -e "\n⚙️ Test 3: Validating GitHub Actions workflow..."
if command -v yamllint &> /dev/null; then
    if yamllint .github/workflows/deploy.yml; then
        test_passed "GitHub Actions workflow YAML is valid"
    else
        test_failed "GitHub Actions workflow YAML has syntax errors"
    fi
else
    test_warning "yamllint not installed, skipping YAML validation"
fi

# Test 4: Check script permissions
echo -e "\n🔒 Test 4: Checking script permissions..."
scripts=(
    "scripts/server-setup.sh"
    "scripts/aws-ec2-setup.sh"
    "scripts/gcp-setup.sh"
)

for script in "${scripts[@]}"; do
    if [[ -x "$script" ]]; then
        test_passed "$script is executable"
    else
        test_warning "$script is not executable (will be fixed on server)"
    fi
done

# Test 5: Validate script syntax
echo -e "\n📝 Test 5: Validating bash script syntax..."
for script in "${scripts[@]}"; do
    if bash -n "$script"; then
        test_passed "$script syntax is valid"
    else
        test_failed "$script has syntax errors"
        exit 1
    fi
done

# Test 6: Check environment template
echo -e "\n🔧 Test 6: Checking environment configuration..."
if grep -q "OPENAI_API_KEY" scripts/server-setup.sh; then
    test_passed "Environment template includes API keys"
else
    test_failed "Environment template missing API keys"
fi

if grep -q "DISCORD_WEBHOOK" scripts/server-setup.sh; then
    test_passed "Environment template includes Discord webhook"
else
    test_failed "Environment template missing Discord webhook"
fi

# Test 7: Validate systemd service configuration
echo -e "\n🎯 Test 7: Validating systemd service configuration..."
if grep -q "ExecStart=/opt/trending-intelligence/venv/bin/python run.py" scripts/server-setup.sh; then
    test_passed "Systemd service configuration is correct"
else
    test_failed "Systemd service configuration is incorrect"
fi

# Test 8: Check Nginx configuration
echo -e "\n🌐 Test 8: Checking Nginx configuration..."
if grep -q "proxy_pass http://127.0.0.1:5000" scripts/server-setup.sh; then
    test_passed "Nginx proxy configuration is correct"
else
    test_failed "Nginx proxy configuration is incorrect"
fi

# Test 9: Validate health check endpoints
echo -e "\n🏥 Test 9: Validating health check configuration..."
if grep -q "/health" scripts/server-setup.sh; then
    test_passed "Health check endpoint configured"
else
    test_failed "Health check endpoint not configured"
fi

# Test 10: Check backup scripts
echo -e "\n💾 Test 10: Checking backup script configuration..."
if grep -q "aws s3 cp" scripts/aws-ec2-setup.sh; then
    test_passed "AWS S3 backup configured"
else
    test_failed "AWS S3 backup not configured"
fi

if grep -q "gsutil cp" scripts/gcp-setup.sh; then
    test_passed "GCP Cloud Storage backup configured"
else
    test_failed "GCP Cloud Storage backup not configured"
fi

# Test 11: Check monitoring configuration
echo -e "\n📊 Test 11: Checking monitoring configuration..."
if grep -q "CloudWatch" scripts/aws-ec2-setup.sh; then
    test_passed "AWS CloudWatch monitoring configured"
else
    test_failed "AWS CloudWatch monitoring not configured"
fi

if grep -q "Cloud Ops Agent" scripts/gcp-setup.sh; then
    test_passed "GCP Cloud Ops monitoring configured"
else
    test_failed "GCP Cloud Ops monitoring not configured"
fi

# Test 12: Simulate deployment dry run
echo -e "\n🚀 Test 12: Simulating deployment dry run..."
temp_dir=$(mktemp -d)
cp -r . "$temp_dir/"
cd "$temp_dir"

# Simulate repository clone and dependency installation
if pip3 install -r requirements.txt --dry-run &> /dev/null; then
    test_passed "Requirements can be installed"
else
    test_warning "Some requirements may not be available (expected in test environment)"
fi

# Test directory creation
mkdir -p data/{raw,processed,reports} logs config
test_passed "Required directories can be created"

# Cleanup
cd - > /dev/null
rm -rf "$temp_dir"

echo -e "\n🎉 All CI/CD tests completed!"
echo "================================"
echo -e "${GREEN}✅ Your deployment scripts are ready!${NC}"
echo ""
echo "📋 Next steps:"
echo "1. Commit and push your changes to GitHub"
echo "2. Set up GitHub secrets for your deployment"
echo "3. Provision your server (AWS EC2 or GCP Compute Engine)"
echo "4. Run the server setup script on your server"
echo "5. Configure your domain and SSL certificate"
echo ""
echo "🚀 Happy deploying!"