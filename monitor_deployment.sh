#!/bin/bash

echo "🔍 Torah-Sod Deployment Monitor"
echo "================================"

# Function to check instance refresh status
check_refresh_status() {
    echo "📊 Instance Refresh Status:"
    aws autoscaling describe-instance-refreshes \
        --auto-scaling-group-name torah-sod-dev-asg \
        --region us-east-1 \
        --profile yahav \
        --query 'InstanceRefreshes[0].{Status:Status,PercentageComplete:PercentageComplete,StatusReason:StatusReason}' \
        --output table
}

# Function to check ASG instances
check_asg_instances() {
    echo "🖥️ Auto Scaling Group Instances:"
    aws autoscaling describe-auto-scaling-instances \
        --region us-east-1 \
        --profile yahav \
        --query 'AutoScalingInstances[?AutoScalingGroupName==`torah-sod-dev-asg`].{InstanceId:InstanceId,LifecycleState:LifecycleState,HealthStatus:HealthStatus,LaunchTemplate:LaunchTemplate.Version}' \
        --output table
}

# Function to check ALB target health
check_alb_health() {
    echo "🎯 ALB Target Health:"
    TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
        --names torah-sod-dev-tg \
        --region us-east-1 \
        --profile yahav \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    aws elbv2 describe-target-health \
        --target-group-arn $TARGET_GROUP_ARN \
        --region us-east-1 \
        --profile yahav \
        --query 'TargetHealthDescriptions[].{Target:Target.Id,Health:TargetHealth.State,Description:TargetHealth.Description}' \
        --output table
}

# Function to check CloudWatch logs for user-data
check_user_data_logs() {
    echo "📝 Recent User-Data Log Entries:"
    aws logs filter-log-events \
        --log-group-name "/aws/ec2/torah-sod-dev" \
        --region us-east-1 \
        --profile yahav \
        --start-time $(date -d '30 minutes ago' +%s)000 \
        --filter-pattern "user-data" \
        --query 'events[-5:].{Time:timestamp,Message:message}' \
        --output table 2>/dev/null || echo "No recent user-data logs found"
}

# Function to test application endpoint
test_application() {
    echo "🌐 Application Health Test:"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    curl -s -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
        http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/health || echo "Health endpoint failed"
    
    echo -e "\nTesting performance endpoint..."
    curl -s http://torah-sod-dev-alb-1291999354.us-east-1.elb.amazonaws.com/api/performance | jq '.performance_config.max_workers' 2>/dev/null || echo "Performance endpoint not ready"
}

# Main monitoring loop
while true; do
    clear
    echo "🔍 Torah-Sod Deployment Monitor - $(date)"
    echo "========================================"
    
    check_refresh_status
    echo
    
    check_asg_instances
    echo
    
    check_alb_health
    echo
    
    check_user_data_logs
    echo
    
    test_application
    echo
    
    echo "Press Ctrl+C to exit. Refreshing in 30 seconds..."
    sleep 30
done