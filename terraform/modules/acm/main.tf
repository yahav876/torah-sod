# Request a certificate for the wildcard domain only
resource "aws_acm_certificate" "cert" {
  domain_name               = "*.${var.domain_name}"
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cert"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Create DNS validation records in Route53
resource "aws_route53_record" "cert_validation" {
  # Use count instead of for_each to avoid conflicts with existing records
  count = 1

  zone_id = var.zone_id
  name    = tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_name
  type    = tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_type
  records = [tolist(aws_acm_certificate.cert.domain_validation_options)[0].resource_record_value]
  ttl     = 60
}

# Wait for certificate validation to complete
resource "aws_acm_certificate_validation" "cert" {
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [aws_route53_record.cert_validation[0].fqdn]
}
