#!/bin/bash
# Script to migrate Terraform backend resources from torah-sod to tzfanim

set -e

AWS_PROFILE="yahav"
AWS_REGION="us-east-1"
OLD_BUCKET_NAME="torah-sod-terraform-state"
OLD_DYNAMODB_TABLE="torah-sod-terraform-locks"
NEW_BUCKET_NAME="tzfanim-terraform-state"
NEW_DYNAMODB_TABLE="tzfanim-terraform-locks"

echo "Setting up new Terraform backend resources..."

# Create new S3 bucket for state
aws s3api create-bucket \
    --bucket $NEW_BUCKET_NAME \
    --region $AWS_REGION \
    --profile $AWS_PROFILE 2>/dev/null || echo "Bucket already exists"

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket $NEW_BUCKET_NAME \
    --versioning-configuration Status=Enabled \
    --profile $AWS_PROFILE

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket $NEW_BUCKET_NAME \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }' \
    --profile $AWS_PROFILE

# Block public access
aws s3api put-public-access-block \
    --bucket $NEW_BUCKET_NAME \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
    --profile $AWS_PROFILE

# Create new DynamoDB table for state locking
aws dynamodb create-table \
    --table-name $NEW_DYNAMODB_TABLE \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 \
    --region $AWS_REGION \
    --profile $AWS_PROFILE 2>/dev/null || echo "DynamoDB table already exists"

echo "New Terraform backend resources created!"
echo "S3 Bucket: $NEW_BUCKET_NAME"
echo "DynamoDB Table: $NEW_DYNAMODB_TABLE"

# Copy state files from old bucket to new bucket
echo "Copying state files from old bucket to new bucket..."
aws s3 sync s3://$OLD_BUCKET_NAME/ s3://$NEW_BUCKET_NAME/ --profile $AWS_PROFILE

echo "Migration complete!"
echo ""
echo "To use the new backend, update the backend configuration in terraform/environments/dev/main.tf:"
echo ""
echo "  backend \"s3\" {"
echo "    bucket         = \"$NEW_BUCKET_NAME\""
echo "    key            = \"dev/terraform.tfstate\""
echo "    region         = \"$AWS_REGION\""
echo "    encrypt        = true"
echo "    dynamodb_table = \"$NEW_DYNAMODB_TABLE\""
echo "    profile        = \"$AWS_PROFILE\""
echo "  }"
echo ""
echo "Then run 'tofu init' to migrate the state to the new backend."
