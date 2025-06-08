# Tzfanim AWS Deployment Guide

## Architecture Overview

The application is deployed on AWS with the following components:
- **ALB (Application Load Balancer)**: Routes traffic to EC2 instances
- **EC2 Auto Scaling Group**: Runs Docker containers (1-3 instances based on load)
- **RDS PostgreSQL**: Managed database for persistent storage
- **ElastiCache Redis**: Caching and Celery message broker
- **VPC**: Network isolation with public/private subnets
- **Route53**: DNS management for domain
- **ACM**: SSL/TLS certificate management with automatic validation

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with profile "yahav"
3. **Terraform** >= 1.5.0
4. **GitHub repository** with the code
5. **SSH Key Pair** created in AWS Console

## Initial Setup

### 1. Create SSH Key Pair

```bash
# In AWS Console: EC2 → Key Pairs → Create key pair
# Name: tzfanim-dev-key
# Download the .pem file and save it securely
```

### 2. Set up Terraform Backend

```bash
cd terraform
./setup-backend.sh
```

This creates:
- S3 bucket for Terraform state
- DynamoDB table for state locking

### 3. Set up ECR Repository

```bash
./scripts/setup-ecr.sh
```

### 4. Configure GitHub Secrets

Add these secrets to your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### 5. Update Configuration

Edit `terraform/environments/dev/main.tf`:
```hcl
locals {
  github_repo = "https://github.com/YOUR_USERNAME/tzfanim.git"  # Update this!
}
```

## Deployment

### Manual Deployment

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Apply changes
terraform apply
```

### Automated Deployment

Push to the `dev` branch:
```bash
git push origin dev
```

This triggers the GitHub Actions pipeline that:
1. Builds Docker image
2. Pushes to ECR
3. Runs Terraform
4. Updates EC2 instances
5. Performs health checks

## Access the Application

After deployment:
1. Get the ALB DNS name:
   ```bash
   terraform output alb_dns_name
   ```
2. Access: `http://<alb-dns-name>`

## Instance Management

### SSH Access

```bash
# Get instance IP
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=tzfanim" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text \
  --profile yahav

# SSH to instance
ssh -i path/to/tzfanim-dev-key.pem ubuntu@<instance-ip>
```

### View Logs

```bash
# On the instance
docker logs tzfanim-tzfanim-search-1
docker logs tzfanim-celery-worker-1
```

### Update Application

The instances automatically pull and run the latest code from GitHub on startup.
To manually update:

```bash
# SSH to instance
cd /opt/tzfanim
git pull origin dev
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

## Monitoring

### CloudWatch Logs

Logs are automatically sent to CloudWatch:
- Log Group: `/aws/ec2/tzfanim-dev`
- Streams: `{instance-id}/app`, `{instance-id}/docker`

### Metrics

CloudWatch metrics include:
- CPU utilization
- Memory usage
- Disk usage
- Application metrics (via Prometheus)

### Auto Scaling

The Auto Scaling Group automatically:
- Scales up when CPU > 80% for 5 minutes
- Scales down when CPU < 20% for 5 minutes
- Maintains 1-3 instances

## Cost Optimization

### Dev Environment
- t3.xlarge EC2: ~$120/month
- db.t3.micro RDS: ~$15/month
- cache.t3.micro ElastiCache: ~$13/month
- ALB: ~$20/month
- **Total: ~$170/month**

### Cost Saving Tips
1. Stop instances when not in use
2. Use scheduled scaling for off-hours
3. Consider smaller instance types if load permits

## Troubleshooting

### Application Not Starting
```bash
# Check user-data script logs
sudo tail -f /var/log/cloud-init-output.log

# Check Docker status
docker ps
docker logs <container-name>
```

### Database Connection Issues
```bash
# Test connection from instance
docker exec -it tzfanim-tzfanim-search-1 bash
apt-get update && apt-get install -y postgresql-client
psql -h <rds-endpoint> -U torah_user -d torah_db
```

### Health Check Failing
```bash
# Test health endpoint
curl http://localhost/api/health
```

## Security Best Practices

1. **Restrict SSH Access**: Update security group to allow only your IP
2. **Use HTTPS**: Add ACM certificate and update ALB listener
3. **Rotate Credentials**: Use AWS Secrets Manager for sensitive data
4. **Enable WAF**: Add AWS WAF to ALB for additional protection
5. **Regular Updates**: Keep Docker images and packages updated

## Destroy Infrastructure

To remove all resources:
```bash
cd terraform/environments/dev
terraform destroy
```

⚠️ **Warning**: This will delete all data including RDS database!

## Next Steps

1. Set up production environment in `terraform/environments/prod`
2. Add monitoring with CloudWatch dashboards
3. Implement backup strategy for RDS
4. Add CI/CD tests before deployment
5. Configure HTTPS with automatic certificate renewal
