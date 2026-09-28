# ============================================================
# APPLICATION LOAD BALANCER
# ============================================================

resource "aws_lb" "banking" {
  name               = "banking-support-alb"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    aws_security_group.alb.id
  ]

  subnets = var.public_subnets

  enable_deletion_protection = false

  tags = {
    Name      = "banking-support-alb"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# MAIN BACKEND TARGET GROUP
# ============================================================

resource "aws_lb_target_group" "main_backend" {
  name        = "banking-main-backend"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"

  vpc_id = data.aws_vpc.existing.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/api/health"
    protocol            = "HTTP"
    matcher             = "200"
  }

  tags = {
    Name      = "banking-main-backend"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# HTTP LISTENER
# ============================================================

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.banking.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}


resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.banking.arn
  port              = 443
  protocol          = "HTTPS"

  ssl_policy = "ELBSecurityPolicy-TLS13-1-2-2021-06"

  certificate_arn = aws_acm_certificate.payanams.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main_backend.arn
  }

  depends_on = [
    aws_acm_certificate_validation.payanams
  ]
}