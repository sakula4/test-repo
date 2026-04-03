# Output values from the Load Balancer configuration

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.main.arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "load_balancer_security_group_id" {
  description = "Security group ID of the Application Load Balancer"
  value       = aws_security_group.alb.id
}

# Listener outputs
output "https_listener_arn" {
  description = "ARN of the HTTPS listener (null if no SSL certificate provided)"
  value       = var.ssl_certificate_arn != null ? aws_lb_listener.https[0].arn : null
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

# Target Group outputs for gw360api
output "gw360api_blue_target_group_arn" {
  description = "ARN of the gw360api blue target group"
  value       = aws_lb_target_group.gw360api_blue.arn
}

output "gw360api_green_target_group_arn" {
  description = "ARN of the gw360api green target group"
  value       = aws_lb_target_group.gw360api_green.arn
}

output "gw360api_blue_target_group_name" {
  description = "Name of the gw360api blue target group"
  value       = aws_lb_target_group.gw360api_blue.name
}

output "gw360api_green_target_group_name" {
  description = "Name of the gw360api green target group"
  value       = aws_lb_target_group.gw360api_green.name
}

# Target Group outputs for gw360ui
output "gw360ui_blue_target_group_arn" {
  description = "ARN of the gw360ui blue target group"
  value       = aws_lb_target_group.gw360ui_blue.arn
}

output "gw360ui_green_target_group_arn" {
  description = "ARN of the gw360ui green target group"
  value       = aws_lb_target_group.gw360ui_green.arn
}

output "gw360ui_blue_target_group_name" {
  description = "Name of the gw360ui blue target group"
  value       = aws_lb_target_group.gw360ui_blue.name
}

output "gw360ui_green_target_group_name" {
  description = "Name of the gw360ui green target group"
  value       = aws_lb_target_group.gw360ui_green.name
}

# Listener Rule outputs
output "gw360api_listener_rule_arn" {
  description = "ARN of the gw360api listener rule"
  value       = aws_lb_listener_rule.gw360api.arn
}

output "gw360ui_listener_rule_arn" {
  description = "ARN of the gw360ui listener rule"  
  value       = aws_lb_listener_rule.gw360ui.arn
}

# Current traffic weights (for reference)
output "gw360api_traffic_weights" {
  description = "Current traffic weights for gw360api"
  value = {
    blue  = var.gw360api_blue_weight
    green = var.gw360api_green_weight
  }
}

output "gw360ui_traffic_weights" {
  description = "Current traffic weights for gw360ui"
  value = {
    blue  = var.gw360ui_blue_weight
    green = var.gw360ui_green_weight
  }
}

# Configuration summary
output "configuration_summary" {
  description = "Summary of the load balancer configuration"
  value = {
    load_balancer_name = aws_lb.main.name
    environment       = var.environment
    gw360api_host     = var.gw360api_host
    gw360ui_host      = var.gw360ui_host
    applications = {
      gw360api = {
        blue_weight  = var.gw360api_blue_weight
        green_weight = var.gw360api_green_weight
      }
      gw360ui = {
        blue_weight  = var.gw360ui_blue_weight
        green_weight = var.gw360ui_green_weight
      }
    }
  }
}