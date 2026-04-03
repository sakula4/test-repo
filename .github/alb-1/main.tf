# Application Load Balancer with Host-based routing and Weighted Target Groups
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources for existing infrastructure
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["gia-acuity-sbx-ue1-apps"]
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  filter {
    name   = "tag:Type"
    values = ["public"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
  filter {
    name   = "tag:Type"
    values = ["private"]
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-${var.app_name}-alb-"
  vpc_id      = data.aws_vpc.main.id
  description = "Security group for ${var.app_name} Application Load Balancer"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.environment}-${var.app_name}-alb-sg"
    Environment = var.environment
    Application = var.app_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.public.ids

  enable_deletion_protection = var.enable_deletion_protection

  # access_logs {
  #   bucket  = var.access_logs_bucket
  #   prefix  = "alb/${var.environment}-${var.app_name}"
  #   enabled = var.enable_access_logs
  # }

  tags = {
    Name        = "${var.environment}-${var.app_name}-alb"
    Environment = var.environment
    Application = var.app_name
  }
}

# Target Groups for gw360api (Blue/Green)
resource "aws_lb_target_group" "gw360api_blue" {
  name     = "${var.environment}-gw360api-blue-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.environment}-gw360api-blue-tg"
    Environment = var.environment
    Application = "gw360api"
    Deployment  = "blue"
  }
}

resource "aws_lb_target_group" "gw360api_green" {
  name     = "${var.environment}-gw360api-green-tg"
  port     = 8080
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.environment}-gw360api-green-tg"
    Environment = var.environment
    Application = "gw360api"
    Deployment  = "green"
  }
}

# Target Groups for gw360ui (Blue/Green)
resource "aws_lb_target_group" "gw360ui_blue" {
  name     = "${var.environment}-gw360ui-blue-tg"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.environment}-gw360ui-blue-tg"
    Environment = var.environment
    Application = "gw360ui"
    Deployment  = "blue"
  }
}

resource "aws_lb_target_group" "gw360ui_green" {
  name     = "${var.environment}-gw360ui-green-tg"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.environment}-gw360ui-green-tg"
    Environment = var.environment
    Application = "gw360ui"
    Deployment  = "green"
  }
}

# HTTPS Listener (conditional - only created if SSL certificate is provided)
resource "aws_lb_listener" "https" {
  count = var.ssl_certificate_arn != null ? 1 : 0
  
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.ssl_certificate_arn

  # Default action - return 404
  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }

  tags = {
    Name        = "${var.environment}-${var.app_name}-https-listener"
    Environment = var.environment
    Application = var.app_name
  }
}

# HTTP Listener (redirect to HTTPS if certificate exists, otherwise serve traffic)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  dynamic "default_action" {
    for_each = var.ssl_certificate_arn != null ? [1] : []
    content {
      type = "redirect"
      redirect {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }

  dynamic "default_action" {
    for_each = var.ssl_certificate_arn == null ? [1] : []
    content {
      type = "fixed-response"
      fixed_response {
        content_type = "text/plain"
        message_body = "Not Found"
        status_code  = "404"
      }
    }
  }

  tags = {
    Name        = "${var.environment}-${var.app_name}-http-listener"
    Environment = var.environment
    Application = var.app_name
  }
}

# Listener Rule for gw360api
resource "aws_lb_listener_rule" "gw360api" {
  listener_arn = var.ssl_certificate_arn != null ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 100

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.gw360api_blue.arn
        weight = var.gw360api_blue_weight
      }
      target_group {
        arn    = aws_lb_target_group.gw360api_green.arn
        weight = var.gw360api_green_weight
      }
      stickiness {
        enabled  = false
        duration = 1
      }
    }
  }

  condition {
    host_header {
      values = [var.gw360api_host]
    }
  }

  tags = {
    Name        = "${var.environment}-gw360api-rule"
    Environment = var.environment
    Application = "gw360api"
  }
}

# Listener Rule for gw360ui
resource "aws_lb_listener_rule" "gw360ui" {
  listener_arn = var.ssl_certificate_arn != null ? aws_lb_listener.https[0].arn : aws_lb_listener.http.arn
  priority     = 200

  action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.gw360ui_blue.arn
        weight = var.gw360ui_blue_weight
      }
      target_group {
        arn    = aws_lb_target_group.gw360ui_green.arn
        weight = var.gw360ui_green_weight
      }
      stickiness {
        enabled  = false
        duration = 1
      }
    }
  }

  condition {
    host_header {
      values = [var.gw360ui_host]
    }
  }

  tags = {
    Name        = "${var.environment}-gw360ui-rule"
    Environment = var.environment
    Application = "gw360ui"
  }
}