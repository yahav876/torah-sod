output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.alb_dns_name
}

output "db_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.elasticache.redis_endpoint
  sensitive   = true
}

output "application_url" {
  description = "Application URL"
  value       = "https://${module.route53.env_domain_record}"
}

output "domain_urls" {
  description = "All configured domain URLs"
  value = {
    root = "https://${module.route53.root_domain_record}"
    www  = "https://${module.route53.www_domain_record}"
    env  = "https://${module.route53.env_domain_record}"
  }
}

output "db_password_ssm_parameter" {
  description = "SSM parameter name for database password"
  value       = module.rds.db_password_ssm_parameter
}

output "route53_name_servers" {
  description = "Name servers for the Route53 hosted zone - update your domain registrar with these"
  value       = module.route53_zone.name_servers
}

output "acm_certificate_status" {
  description = "Status of the ACM certificate"
  value       = data.aws_acm_certificate.wildcard.status
}
