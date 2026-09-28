resource "aws_route53_zone" "payanams" {
  name = "payanams.xyz"

  comment = "Banking Support production DNS"

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

output "payanams_nameservers" {
  value = aws_route53_zone.payanams.name_servers
}

output "payanams_zone_id" {
  value = aws_route53_zone.payanams.zone_id
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.payanams.zone_id
  name    = "api.payanams.xyz"
  type    = "A"

  alias {
    name                   = aws_lb.banking.dns_name
    zone_id                = aws_lb.banking.zone_id
    evaluate_target_health = true
  }
}