terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "torah-sod-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "torah-sod-terraform-locks"
    profile        = "yahav"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = "yahav"

  default_tags {
    tags = {
      Environment = "dev"
      Project     = var.project_name
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  environment = "dev"
  github_repo = "https://github.com/yahav876/torah-sod.git"  # Fixed typo: was .gitls
  domain_name = "torah-sod.com"
}

# Create Route53 Hosted Zone first
module "route53_zone" {
  source = "../../modules/route53-zone"

  domain_name  = local.domain_name
  environment  = local.environment
  project_name = var.project_name
}

# Data source to find the ACM certificate (including PENDING_VALIDATION)
data "aws_acm_certificate" "wildcard" {
  domain      = "*.${local.domain_name}"
  statuses    = ["ISSUED", "PENDING_VALIDATION"]
  most_recent = true
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name       = var.project_name
  environment        = local.environment
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = var.availability_zones
  enable_nat_gateway = true
}

# Security Module
module "security" {
  source = "../../modules/security"

  project_name    = var.project_name
  environment     = local.environment
  vpc_id          = module.vpc.vpc_id
  ssh_allowed_ips = ["0.0.0.0/0"]  # Restrict this to your IP!
}

# ALB Module
module "alb" {
  source = "../../modules/alb"

  project_name          = var.project_name
  environment           = local.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.security.alb_security_group_id
  certificate_arn       = data.aws_acm_certificate.wildcard.status == "ISSUED" ? data.aws_acm_certificate.wildcard.arn : ""
}

# Generate a random password for RDS
resource "random_password" "db" {
  length  = 32
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"  # Exclude /, @, ", and space
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name          = var.project_name
  environment           = local.environment
  db_instance_class     = var.db_instance_class
  private_subnet_ids    = module.vpc.private_subnet_ids
  rds_security_group_id = module.security.rds_security_group_id
  db_password_override  = random_password.db.result
}

# ElastiCache Module
module "elasticache" {
  source = "../../modules/elasticache"

  project_name                  = var.project_name
  environment                   = local.environment
  elasticache_node_type         = var.elasticache_node_type
  private_subnet_ids            = module.vpc.private_subnet_ids
  elasticache_security_group_id = module.security.elasticache_security_group_id
}

# EC2 Module
module "ec2" {
  source = "../../modules/ec2"

  project_name          = var.project_name
  environment           = local.environment
  instance_type         = var.instance_type
  key_pair_name         = var.key_pair_name
  private_subnet_ids    = module.vpc.private_subnet_ids
  ec2_security_group_id = module.security.ec2_security_group_id
  target_group_arn      = module.alb.target_group_arn
  min_size              = 1
  max_size              = 2
  desired_capacity      = 1
  aws_region            = var.aws_region
  db_host               = module.rds.db_host
  db_name               = module.rds.db_name
  db_username           = module.rds.db_username
  db_password           = random_password.db.result
  redis_host            = module.elasticache.redis_primary_endpoint
  docker_image_tag      = "dev"
  github_repo           = local.github_repo
}

# Route 53 Module
module "route53" {
  source = "../../modules/route53"

  domain_name          = local.domain_name
  alb_dns_name         = module.alb.alb_dns_name
  alb_zone_id          = module.alb.alb_zone_id
  environment          = local.environment
  create_env_subdomain = true  # This will create dev.torah-sod.com
}
