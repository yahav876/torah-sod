#!/bin/bash
set -e

# Redirect all output to a log file and CloudWatch
exec > >(tee -a /var/log/user-data.log)
exec 2>&1

echo "[$(date)] Starting user-data script execution..."

# Function for error handling
error_exit() {
    echo "[$(date)] ERROR: $1" >&2
    exit 1
}

# Function for logging with timestamp
log_info() {
    echo "[$(date)] INFO: $1"
}

log_info "User data script starting..."

# Update system
log_info "Updating system packages..."
apt-get update || error_exit "Failed to update package list"
apt-get upgrade -y || error_exit "Failed to upgrade packages"

# Install Docker
log_info "Installing Docker..."
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release || error_exit "Failed to install Docker prerequisites"

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg || error_exit "Failed to add Docker GPG key"

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin || error_exit "Failed to install Docker"

# Ensure Docker is running
systemctl enable docker
systemctl start docker || error_exit "Failed to start Docker"

# Install AWS CLI (only if not already installed)
if ! command -v aws &> /dev/null; then
    log_info "Installing AWS CLI..."
    apt-get install -y unzip
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
else
    log_info "AWS CLI already installed, skipping installation"
fi

# Install CloudWatch Agent (only if not already installed)
if [ ! -f "/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent" ]; then
    log_info "Installing CloudWatch Agent..."
    wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
    dpkg -i -E ./amazon-cloudwatch-agent.deb
else
    log_info "CloudWatch Agent already installed, skipping installation"
fi

# Configure CloudWatch Agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<EOF
{
  "metrics": {
    "namespace": "${project_name}-${environment}",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait",
          "cpu_usage_user",
          "cpu_usage_system"
        ],
        "metrics_collection_interval": 60,
        "totalcpu": false
      },
      "disk": {
        "measurement": [
          "used_percent",
          "inodes_free"
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
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/tzfanim/*.log",
            "log_group_name": "/aws/ec2/${project_name}-${environment}",
            "log_stream_name": "{instance_id}/app",
            "timezone": "UTC"
          },
          {
            "file_path": "/opt/tzfanim/logs/*.log",
            "log_group_name": "/aws/ec2/${project_name}-${environment}",
            "log_stream_name": "{instance_id}/app-docker",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/lib/docker/containers/*/*-json.log",
            "log_group_name": "/aws/ec2/${project_name}-${environment}",
            "log_stream_name": "{instance_id}/docker-containers",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/ec2/${project_name}-${environment}",
            "log_stream_name": "{instance_id}/user-data",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "/aws/ec2/${project_name}-${environment}",
            "log_stream_name": "{instance_id}/cloud-init",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
EOF

# Start CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

# Create app directory and logs
mkdir -p /opt/tzfanim
mkdir -p /var/log/tzfanim

# Clone repository (remove existing directory first if it exists)
log_info "Cloning Tzfanim repository..."
cd /opt
if [ -d "tzfanim" ]; then
    log_info "Removing existing tzfanim directory..."
    rm -rf tzfanim
fi

# Try multiple repository URLs and methods
log_info "Trying to clone repository..."

# Try HTTPS with the provided URL
log_info "Trying HTTPS clone with provided URL: ${github_repo}"
git clone ${github_repo} tzfanim && {
    log_info "Repository cloned successfully with provided URL"
} || {
    # Try HTTPS with explicit URL
    log_info "Trying HTTPS clone with explicit URL..."
    git clone https://github.com/yahav876/torah-sod.git tzfanim && {
        log_info "Repository cloned successfully with explicit HTTPS URL"
    } || {
        # Try to download as a ZIP file as a last resort
        log_info "Git clone failed, trying to download as ZIP..."
        apt-get install -y unzip || log_info "Unzip already installed"
        curl -L https://github.com/yahav876/torah-sod/archive/refs/heads/main.zip -o torah-sod.zip && {
            unzip torah-sod.zip
            mv torah-sod-main tzfanim
            log_info "Repository downloaded as ZIP successfully"
        } || error_exit "Failed to clone or download repository using all methods"
    }
}

cd /opt/tzfanim
git checkout dev || log_info "No dev branch found, using main branch"

# Create logs directory after clone
mkdir -p logs
log_info "Repository cloned successfully"

# Create .env file
cat > .env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_host}:5432/${db_name}
REDIS_URL=redis://${redis_host}:6379/0
CELERY_BROKER_URL=redis://${redis_host}:6379/1
CELERY_RESULT_BACKEND=redis://${redis_host}:6379/2
POSTGRES_PASSWORD=${db_password}
AWS_DEFAULT_REGION=${aws_region}
FLASK_ENV=${environment}
EOF

# Configure Docker logging first
log_info "Configuring Docker logging..."
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker || error_exit "Failed to restart Docker"
sleep 5  # Wait for Docker to fully restart

# Login to ECR
log_info "Logging into ECR..."
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.${aws_region}.amazonaws.com || error_exit "Failed to login to ECR"

# Start the application with proper logging
log_info "Starting Tzfanim application..."
docker compose -f docker-compose.aws.yml up -d || error_exit "Failed to start application containers"

# Wait for containers to start
sleep 15

# Check if containers are running
log_info "Checking container status..."
docker ps -a

# Wait a bit more for application to fully initialize
sleep 10

# Build search index for ultra-fast performance
log_info "Building search index for lightning-fast searches..."
curl -X POST http://localhost/api/admin/build-index \
  -H "Content-Type: application/json" \
  --max-time 300 \
  --retry 3 \
  --retry-delay 10 \
  2>/dev/null || log_info "Search index will be built on first search"

# Create symlink for easier log access (don't fail if no containers yet)
ln -sf /var/lib/docker/containers/*/tzfanim-*.log /opt/tzfanim/logs/ 2>/dev/null || log_info "No Tzfanim containers found yet"

# Setup log rotation
cat > /etc/logrotate.d/tzfanim <<EOF
/var/log/tzfanim/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
EOF

log_info "Tzfanim application deployment completed!"
log_info "Final container status:"
docker ps
log_info "User data script finished successfully"
