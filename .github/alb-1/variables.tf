# Input variables for the Load Balancer configuration

variable "environment" {
  description = "Environment name (dev, uat, prod)"
  type        = string
  validation {
    condition = contains(["dev", "uat", "prod"], var.environment)
    error_message = "Environment must be one of: dev, uat, prod."
  }
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "gw360"
}

variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener (optional - if not provided, only HTTP listener will be created)"
  type        = string
  default     = null
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for the load balancer"
  type        = bool
  default     = true
}

variable "enable_access_logs" {
  description = "Enable access logs for the load balancer"
  type        = bool
  default     = true
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

# Host header configurations
variable "gw360api_host" {
  description = "Host header for gw360api routing"
  type        = string
  default     = "api.gw360.example.com"
}

variable "gw360ui_host" {
  description = "Host header for gw360ui routing"
  type        = string
  default     = "app.gw360.example.com"
}

# Traffic weight configurations for gw360api
variable "gw360api_blue_weight" {
  description = "Traffic weight for gw360api blue target group (0-100)"
  type        = number
  default     = 100
  validation {
    condition     = var.gw360api_blue_weight >= 0 && var.gw360api_blue_weight <= 100
    error_message = "Weight must be between 0 and 100."
  }
}

variable "gw360api_green_weight" {
  description = "Traffic weight for gw360api green target group (0-100)"
  type        = number
  default     = 0
  validation {
    condition     = var.gw360api_green_weight >= 0 && var.gw360api_green_weight <= 100
    error_message = "Weight must be between 0 and 100."
  }
}

# Traffic weight configurations for gw360ui
variable "gw360ui_blue_weight" {
  description = "Traffic weight for gw360ui blue target group (0-100)"
  type        = number
  default     = 100
  validation {
    condition     = var.gw360ui_blue_weight >= 0 && var.gw360ui_blue_weight <= 100
    error_message = "Weight must be between 0 and 100."
  }
}

variable "gw360ui_green_weight" {
  description = "Traffic weight for gw360ui green target group (0-100)"
  type        = number
  default     = 0
  validation {
    condition     = var.gw360ui_green_weight >= 0 && var.gw360ui_green_weight <= 100
    error_message = "Weight must be between 0 and 100."
  }
}

# Optional: Additional tags
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}