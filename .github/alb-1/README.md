# Load Balancer Terraform Module

This Terraform module creates an Application Load Balancer (ALB) with host-based routing and weighted target groups for blue-green deployments.

## Features

- 🔄 **Blue-Green Deployment Support**: Weighted target groups for gradual traffic shifting
- 🌐 **Host-Based Routing**: Route traffic based on host headers (gw360api, gw360ui)
- 🔒 **SSL/TLS Termination**: HTTPS listener with configurable SSL certificate
- 📊 **Health Checks**: Configured health checks for all target groups
- 🛡️ **Security Groups**: Properly configured security groups for ALB access
- 📝 **Access Logs**: Optional ALB access logging to S3

## Architecture

```
Internet → ALB → HTTPS Listener (443) → Rules based on Host Header
                     ├── gw360api.example.com → Blue TG (100%) + Green TG (0%)
                     └── gw360ui.example.com  → Blue TG (100%) + Green TG (0%)
```

## Resources Created

- **Application Load Balancer** with public subnets
- **Security Group** for ALB with HTTP/HTTPS ingress
- **4 Target Groups**: Blue/Green for both gw360api and gw360ui
- **HTTPS Listener** (port 443) with SSL certificate
- **HTTP Listener** (port 80) redirecting to HTTPS
- **2 Listener Rules** for host-based routing

## Usage

### 1. Basic Setup

```hcl
module "load_balancer" {
  source = "./loadbalancers"
  
  environment         = "dev"
  ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
  
  # Host headers
  gw360api_host = "api.dev.example.com"
  gw360ui_host  = "app.dev.example.com"
  
  # Initial weights (100% blue, 0% green)
  gw360api_blue_weight  = 100
  gw360api_green_weight = 0
  gw360ui_blue_weight   = 100
  gw360ui_green_weight  = 0
}
```

### 2. Canary Deployment (10% traffic to new version)

```hcl
module "load_balancer" {
  source = "./loadbalancers"
  
  environment         = "prod"
  ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
  
  # Canary deployment: 90% blue, 10% green
  gw360api_blue_weight  = 90
  gw360api_green_weight = 10
  gw360ui_blue_weight   = 90
  gw360ui_green_weight  = 10
}
```

### 3. Full Deployment Completion

```hcl
module "load_balancer" {
  source = "./loadbalancers"
  
  environment = "prod"
  ssl_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."
  
  # Switch to green (new version)
  gw360api_blue_weight  = 0
  gw360api_green_weight = 100
  gw360ui_blue_weight   = 0
  gw360ui_green_weight  = 100
}
```

## Prerequisites

1. **VPC with subnets** tagged appropriately:
   - Public subnets tagged with `Type = "public"`
   - Private subnets tagged with `Type = "private"`
   - VPC tagged with `Name = "${environment}-vpc"`

2. **SSL Certificate** in AWS Certificate Manager

3. **S3 Bucket** for access logs (optional)

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| `environment` | Environment name (dev, uat, prod) | `string` | Required |
| `ssl_certificate_arn` | ARN of SSL certificate | `string` | Required |
| `gw360api_host` | Host header for API routing | `string` | `"api.gw360.example.com"` |
| `gw360ui_host` | Host header for UI routing | `string` | `"app.gw360.example.com"` |
| `gw360api_blue_weight` | Traffic weight for API blue TG | `number` | `100` |
| `gw360api_green_weight` | Traffic weight for API green TG | `number` | `0` |
| `gw360ui_blue_weight` | Traffic weight for UI blue TG | `number` | `100` |
| `gw360ui_green_weight` | Traffic weight for UI green TG | `number` | `0` |

## Outputs

| Name | Description |
|------|-------------|
| `load_balancer_dns_name` | DNS name of the ALB |
| `gw360api_blue_target_group_arn` | ARN of gw360api blue target group |
| `gw360api_green_target_group_arn` | ARN of gw360api green target group |
| `gw360ui_blue_target_group_arn` | ARN of gw360ui blue target group |
| `gw360ui_green_target_group_arn` | ARN of gw360ui green target group |

## Deployment Workflow

1. **Initial Deployment**: Set blue=100, green=0
2. **Deploy New Version**: Deploy to green target groups
3. **Canary Testing**: Shift small percentage to green (blue=90, green=10)
4. **Gradual Rollout**: Increase green traffic incrementally
5. **Complete Rollout**: Full traffic to green (blue=0, green=100)
6. **Cleanup**: Deploy next version to blue, repeat process

## Health Checks

- **gw360api**: HTTP health check on port 8080, path `/health`
- **gw360ui**: HTTP health check on port 3000, path `/`
- **Thresholds**: 2 successful checks = healthy, 2 failed checks = unhealthy

## Security

- Security group allows HTTP (80) and HTTPS (443) from anywhere
- HTTP traffic automatically redirects to HTTPS
- SSL termination at the load balancer level

## Monitoring

Enable access logs by setting:
```hcl
enable_access_logs = true
access_logs_bucket = "your-s3-bucket-name"
```

## Example Commands

```bash
# Initialize and plan
terraform init
terraform plan -var-file="terraform.tfvars"

# Apply configuration  
terraform apply -var-file="terraform.tfvars"

# Shift traffic to green (canary)
terraform apply -var="gw360api_green_weight=10" -var="gw360api_blue_weight=90"

# Complete rollout to green
terraform apply -var="gw360api_green_weight=100" -var="gw360api_blue_weight=0"
```