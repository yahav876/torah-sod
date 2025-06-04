locals {
  # Use provided zone_id if not looking up, otherwise use the looked up zone_id
  zone_id = var.lookup_hosted_zone ? try(data.aws_route53_zone.main[0].zone_id, null) : var.zone_id
}

# Data source to find the hosted zone
data "aws_route53_zone" "main" {
  count        = var.lookup_hosted_zone ? 1 : 0
  name         = "${var.domain_name}."
  private_zone = false
}


# Create an A record for the root domain
resource "aws_route53_record" "root" {
  zone_id = local.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Create an A record for www subdomain
resource "aws_route53_record" "www" {
  zone_id = local.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Create an A record for the environment-specific subdomain (e.g., dev.torah-sod.com)
resource "aws_route53_record" "env" {
  count   = var.create_env_subdomain ? 1 : 0
  zone_id = local.zone_id
  name    = "${var.environment}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}