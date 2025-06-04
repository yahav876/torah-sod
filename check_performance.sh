#!/bin/bash
echo "=== Torah-Sod Performance Check ==="
echo "ALB Health:"
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names torah-sod-dev-tg --query 'TargetGroups[0].TargetGroupArn' --output text) --region us-east-1 --profile yahav

echo "\nASG Status:"
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names torah-sod-dev-asg --region us-east-1 --profile yahav --query 'AutoScalingGroups[0].{DesiredCapacity:DesiredCapacity,MinSize:MinSize,MaxSize:MaxSize,Instances:length(Instances)}'

echo "\nCloudWatch Alarms:"
aws cloudwatch describe-alarms --alarm-names torah-sod-dev-high-cpu torah-sod-dev-low-cpu --region us-east-1 --profile yahav --query 'MetricAlarms[].{Name:AlarmName,State:StateValue,Reason:StateReason}'
