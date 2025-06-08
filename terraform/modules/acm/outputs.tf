output "certificate_arn" {
  description = "ARN of the issued certificate"
  value       = aws_acm_certificate_validation.cert.certificate_arn
}

output "certificate_status" {
  description = "Status of the certificate"
  value       = aws_acm_certificate.cert.status
}

output "domain_validation_options" {
  description = "Domain validation options for the certificate"
  value       = aws_acm_certificate.cert.domain_validation_options
}
