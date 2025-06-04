variable "domain_name" {
  description = "The domain name to use"
  type        = string
}

variable "lookup_hosted_zone" {
  description = "Try to look up hosted zone (set to false if always creating new)"
  type        = bool
  default     = true
}

variable "zone_id" {
  description = "The zone ID to use (if not looking up)"
  type        = string
  default     = ""
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
