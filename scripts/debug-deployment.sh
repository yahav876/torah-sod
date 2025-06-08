#!/bin/bash
# Script to debug deployment issues

set -e

PROFILE="yahav"
REGION="us-east-1"
PROJECT="tzfanim"
ENV="dev"

echo "🔍 Debugging Tzfanim Deployment..."

# Get ALB and Target Group info
echo -e "\n📊 Getting ALB and Target Group info..."
TG_ARN=$(aws elbv2 describe-target-groups \
  --names "${PROJECT}-${ENV}-tg" \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text \
  --profile $PROFILE \
  --region $REGION 2>/dev/null || echo "")

if [ -z "$TG_ARN" ]; then
  echo "❌ Target group not found!"
  exit 1
fi

# Check target health
echo -e "\n🏥 Checking target health..."
aws elbv2 describe-target-health \
  --target-group-arn $TG_ARN \
  --profile $PROFILE \
  --region $REGION \
  --output table

# Get instance IDs
INSTANCE_IDS=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=$PROJECT" "Name=tag:Environment,Values=$ENV" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text \
  --profile $PROFILE \
  --region $REGION)

if [ -z "$INSTANCE_IDS" ]; then
  echo "❌ No running instances found!"
  exit 1
fi

echo -e "\n🖥️  Found instances: $INSTANCE_IDS"

# For each instance
for INSTANCE_ID in $INSTANCE_IDS; do
  echo -e "\n📝 Instance: $INSTANCE_ID"
  
  # Get instance details
  aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[PrivateIpAddress,State.Name,LaunchTime]' \
    --output table \
    --profile $PROFILE \
    --region $REGION
  
  echo -e "\n🔗 Connecting to instance via SSM..."
  echo "Run these commands after connecting:"
  echo "  1. Check user-data log: sudo tail -100 /var/log/cloud-init-output.log"
  echo "  2. Check Docker: docker ps"
  echo "  3. Check nginx: docker logs tzfanim-nginx-1"
  echo "  4. Check app: docker logs tzfanim-torah-search-1"
  echo "  5. Test health: curl -v http://localhost/api/health"
  echo ""
  echo "Press Enter to connect to $INSTANCE_ID (or Ctrl+C to skip)..."
  read
  
  aws ssm start-session --target $INSTANCE_ID --profile $PROFILE --region $REGION
done

# Check CloudWatch Logs
echo -e "\n☁️  Recent CloudWatch Logs..."
LOG_GROUP="/aws/ec2/${PROJECT}-${ENV}"

# Check if log group exists
if aws logs describe-log-groups --log-group-name-prefix $LOG_GROUP --profile $PROFILE --region $REGION --query 'logGroups[0].logGroupName' --output text | grep -q $LOG_GROUP; then
  echo "Recent user-data logs:"
  aws logs tail $LOG_GROUP --profile $PROFILE --region $REGION --since 10m --filter-pattern "user-data" || true
else
  echo "Log group $LOG_GROUP not found. Logs might not be configured yet."
fi
