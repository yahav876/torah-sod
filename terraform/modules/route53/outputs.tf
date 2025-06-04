output "root_domain_record" {
  value = aws_route53_record.root.fqdn
}

output "www_domain_record" {
  value = aws_route53_record.www.fqdn
}

output "env_domain_record" {
  value = var.create_env_subdomain ? aws_route53_record.env[0].fqdn : ""
}

output "zone_id" {
  value = local.zone_id
}
