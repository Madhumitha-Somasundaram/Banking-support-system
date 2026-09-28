resource "aws_acm_certificate" "payanams" {
  domain_name       = "payanams.xyz"
  validation_method = "DNS"

  subject_alternative_names = [
    "api.payanams.xyz"
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.payanams.domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = aws_route53_zone.payanams.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60

  records = [
    each.value.record
  ]

  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "payanams" {
  certificate_arn = aws_acm_certificate.payanams.arn

  validation_record_fqdns = [
    for record in aws_route53_record.acm_validation :
    record.fqdn
  ]
}

output "payanams_certificate_arn" {
  value = aws_acm_certificate.payanams.arn
}