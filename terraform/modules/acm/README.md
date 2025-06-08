# ACM Certificate Module

This module creates an AWS Certificate Manager (ACM) certificate for a domain and automatically validates it using DNS validation records in Route53.

## Features

- Creates an ACM certificate for a domain and its wildcard subdomains
- Automatically adds DNS validation records to a Route53 hosted zone
- Waits for certificate validation to complete
- Provides the certificate ARN for use with other AWS services (like ALB)

## Usage

```hcl
module "acm" {
  source = "../../modules/acm"

  domain_name  = "example.com"
  zone_id      = module.route53_zone.zone_id
  project_name = var.project_name
  environment  = "dev"
}
```

## Inputs

| Name | Description | Type | Required |
|------|-------------|------|:--------:|
| domain_name | Domain name for the certificate | string | yes |
| zone_id | Route53 hosted zone ID | string | yes |
| project_name | Name of the project | string | yes |
| environment | Environment name | string | yes |

## Outputs

| Name | Description |
|------|-------------|
| certificate_arn | ARN of the issued certificate |
| certificate_status | Status of the certificate |
| domain_validation_options | Domain validation options for the certificate |

## How It Works

1. The module requests a certificate for the domain and its wildcard subdomains (e.g., example.com and *.example.com)
2. It creates DNS validation records in the specified Route53 hosted zone
3. It waits for the certificate validation to complete
4. The certificate ARN is output for use with other AWS services

This module ensures that your domain has a valid SSL/TLS certificate that can be used with AWS services like ALB, CloudFront, etc.
