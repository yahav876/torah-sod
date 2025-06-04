variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "elasticache_node_type" {
  description = "ElastiCache node type"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "elasticache_security_group_id" {
  description = "ElastiCache security group ID"
  type        = string
}
