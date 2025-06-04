variable "domain_name" {
  description = "The domain name to use"
  type        = string
}

variable "alb_dns_name" {
  description = "The DNS name of the ALB"
  type        = string
}

variable "alb_zone_id" {
  description = "The zone ID of the ALB"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "create_env_subdomain" {
  description = "Whether to create environment-specific subdomain"
  type        = bool
  default     = true
}
