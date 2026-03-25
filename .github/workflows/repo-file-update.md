---
name: Repo File Update
description: Periodically checks out the repository, makes modifications to tracked files, and creates a pull request with the changes.
on:
  schedule:
    - cron: "0 9 * * 1"  # Weekly on Monday at 9 AM UTC
  workflow_dispatch:
permissions:
  contents: read
  pull-requests: read
  issues: read
timeout-minutes: 20
tools:
  github:
    toolsets: [default]
  edit:
safe-outputs:
  create-pull-request:
    title-prefix: "[automated] "
    labels: [automated, file-update]
    draft: false
    if-no-changes: warn
---

# Repo File Update Workflow

You are an automated assistant responsible for updating the files configuration as listed out in the tasks.

## Repository Context

- Repository: `${{ github.repository }}`
- Triggered by: `${{ github.event_name }}`

## Your Task

1. **Inspect the repository** to understand its current state and identify the load balancer configuration files.

2. **Configure AWS credentials** using environment variables or AWS CLI profile:
   ```bash
   # Ensure AWS credentials are configured (via environment, profile, or OIDC)
   export AWS_DEFAULT_REGION="us-east-1"
   
   # Test AWS access
   aws sts get-caller-identity
   ```

3. **Discover current load balancer weights** by running these commands:
   ```bash
   # Get Load Balancer ARN
   LB_ARN=$(aws elbv2 describe-load-balancers --names "dev-gw360-alb" --query 'LoadBalancers[0].LoadBalancerArn' --output text)
   
   # Get HTTP Listener ARN
   LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn "$LB_ARN" --query 'Listeners[?Port==`80`].ListenerArn' --output text)
   
   # Get rules and weights in JSON format
   aws elbv2 describe-rules --listener-arn "$LISTENER_ARN" --output json | jq '[.Rules[] | select(.Priority != "default") | {Priority: .Priority | tonumber, HostHeader: .Conditions[0].Values[0], TargetGroups: [.Actions[0].ForwardConfig.TargetGroups[] | {TargetGroupName: (.TargetGroupArn | split("/")[1]), Weight: .Weight}]}]'
   ```

4. **Update the configuration file** `loadbalancer/_config/dev.us-east-1.yaml`:
   - Find the target group weight configurations under `apps_alb.rules` and `apps_alb.gw360ui`
   - For each application:
     - **gw360api**: Look for `target_groups` array under `apps_alb.rules.actions[0]`
     - **gw360ui**: Look for `target_groups` array under `apps_alb.gw360ui.actions[0]`
   - Swap the weights between the two target groups:
     - If weights are [0, 100] → change to [100, 0]
     - If weights are [100, 0] → change to [0, 100]
     - If weights are [90, 10] → change to [10, 90]
   - This simulates toggling between blue-green deployments

5. **Create a pull request** with all the changes:
   - Title should be: "chore: automated blue-green weight toggle YYYY-MM-DD"
   - Body should include:
     - Summary of weight changes made
     - Current AWS load balancer state vs configuration file
     - Which applications were affected (gw360api, gw360ui)
   - The PR is created automatically via the `create-pull-request` safe output

## Guidelines

- **AWS Authentication**: AWS credentials must be available through environment variables, IAM roles, or OIDC. Test access with `aws sts get-caller-identity`
- **Validation**: Ensure the total weights for each application equal 100%
- **Safety**: Only update weights if the configuration file `loadbalancer/_config/dev.us-east-1.yaml` exists and has the expected YAML structure with `apps_alb` section
- **Documentation**: Include before/after weight values in the PR description
- **Error handling**: If AWS CLI commands fail, document the error and exit gracefully
- **No changes**: If weights are already in the desired state, do not create a pull request
- **Date format**: Use ISO 8601 date format (YYYY-MM-DD) in commit messages and PR titles
