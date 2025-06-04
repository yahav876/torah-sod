#!/bin/bash
# Script to set up ECR repository

set -e

AWS_PROFILE="yahav"
AWS_REGION="us-east-1"
REPOSITORY_NAME="torah-sod"

echo "Setting up ECR repository..."

# Create ECR repository
aws ecr create-repository \
    --repository-name $REPOSITORY_NAME \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    2>/dev/null || echo "Repository already exists"

# Set lifecycle policy to keep only last 10 images
aws ecr put-lifecycle-policy \
    --repository-name $REPOSITORY_NAME \
    --lifecycle-policy-text '{
        "rules": [
            {
                "rulePriority": 1,
                "description": "Keep last 10 images",
                "selection": {
                    "tagStatus": "any",
                    "countType": "imageCountMoreThan",
                    "countNumber": 10
                },
                "action": {
                    "type": "expire"
                }
            }
        ]
    }' \
    --region $AWS_REGION \
    --profile $AWS_PROFILE

# Get repository URI
REPO_URI=$(aws ecr describe-repositories \
    --repository-names $REPOSITORY_NAME \
    --region $AWS_REGION \
    --profile $AWS_PROFILE \
    --query 'repositories[0].repositoryUri' \
    --output text)

echo "ECR repository setup complete!"
echo "Repository URI: $REPO_URI"
