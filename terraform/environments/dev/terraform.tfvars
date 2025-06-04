project_name = "torah-sod"
aws_region   = "us-east-1"
availability_zones = ["us-east-1a", "us-east-1b"]

# Instance configuration
instance_type = "t3.2xlarge"  # 8 vCPU, 32GB RAM
key_pair_name = "torah-sod-dev-key"  # Create this in AWS Console first!

# Database configuration
db_instance_class = "db.t3.micro"  # For dev, use smaller instance

# ElastiCache configuration
elasticache_node_type = "cache.t3.micro"  # For dev, use smaller instance

# Domain and certificate (optional)
# domain_name = "torah-sod-dev.example.com"
# certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
