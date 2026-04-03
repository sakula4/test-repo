# ECS Task Definition Workflow

This workflow creates and registers an AWS ECS Task Definition using a templatized approach.

## Overview

The workflow uses a template file ([task-definition-template.json](task-definition-template.json)) with placeholders that get replaced with values provided as workflow inputs. This allows you to create task definitions dynamically without manually editing JSON files.

## Files

- **`.github/workflows/create-task-definition.yml`** - The GitHub Actions workflow
- **`task-definition-template.json`** - The templatized task definition with placeholders

## Workflow Inputs

The workflow accepts the following inputs via `workflow_dispatch`:

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `task_family` | Task Definition Family Name | Yes | `gw360api` |
| `app_name` | Application Container Name | Yes | `gw360api` |
| `app_image_uri` | Application Image URI | Yes | - |
| `log_group_name` | CloudWatch Log Group Name | Yes | `/aws/ecs/containerinsights/gia-dev-ue1-gw360-api-logs` |
| `aws_region` | AWS Region | Yes | `us-east-1` |

## Template Placeholders

The template uses the following placeholders:

- `{{TASK_FAMILY}}` - Replaced with the task definition family name
- `{{APP_NAME}}` - Replaced with the application container name
- `{{APP_IMAGE_URI}}` - Replaced with the application image URI
- `{{LOG_GROUP_NAME}}` - Replaced with the CloudWatch log group name

## Usage

### Running the Workflow

1. Navigate to the **Actions** tab in your GitHub repository
2. Select **"Create ECS Task Definition"** from the workflows list
3. Click **"Run workflow"**
4. Fill in the required inputs:
   - **Task Family Name**: e.g., `gw360api`
   - **Application Container Name**: e.g., `gw360api`
   - **Application Image URI**: e.g., `350828950339.dkr.ecr.us-east-1.amazonaws.com/gia-gw360-api:dev-af0c7ef`
   - **CloudWatch Log Group Name**: e.g., `/aws/ecs/containerinsights/gia-dev-ue1-gw360-api-logs`
   - **AWS Region**: e.g., `us-east-1`
5. Click **"Run workflow"**

### Example Input Values

```yaml
task_family: gw360api
app_name: gw360api
app_image_uri: 350828950339.dkr.ecr.us-east-1.amazonaws.com/gia-gw360-api:dev-af0c7ef
log_group_name: /aws/ecs/containerinsights/gia-dev-ue1-gw360-api-logs
aws_region: us-east-1
```

## What the Workflow Does

1. **Checkout Code** - Checks out the repository to access the template file
2. **Generate Task Definition** - Replaces placeholders in the template with input values
3. **Configure AWS Credentials** - Authenticates with AWS using OIDC
4. **Register Task Definition** - Registers the new task definition with AWS ECS
5. **Upload Artifact** - Saves the generated task definition as an artifact (retained for 30 days)
6. **Summary** - Displays a summary with the task definition ARN and revision number

## Prerequisites

### AWS Configuration

1. **AWS Account ID Secret**: The workflow expects `secrets.AWS_ACCOUNT_ID` to be set in your repository
2. **IAM Role**: An IAM role named `github-actions-role` with permissions to:
   - Register ECS task definitions
   - Create CloudWatch log groups
   - Access required secrets in Secrets Manager

### AWS IAM Role Setup

The role should have the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "iam:PassRole"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

## Task Definition Structure

The template includes three containers:

1. **Application Container** (`{{APP_NAME}}`)
   - Main application container
   - Uses the image URI provided as input
   - Configured with health checks and logging via FireLens
   - Environment variables are left empty (to be configured separately)

2. **Log Router Container** (`log-router`)
   - Fluent Bit for log aggregation
   - Sends logs to CloudWatch via FireLens
   - Configured with Dynatrace integration

3. **Dynatrace OneAgent Container** (`install-oneagent`)
   - Init container for Dynatrace monitoring
   - Downloads and installs the OneAgent

## Customization

### Modifying the Template

To modify the template, edit [task-definition-template.json](task-definition-template.json):

1. Add new placeholders using the format `{{PLACEHOLDER_NAME}}`
2. Update the workflow file to add corresponding inputs
3. Update the sed replacement commands in the "Generate Task Definition" step

### Adding Environment Variables

To add environment variables to the application container:

1. Edit the template and add environment variables in the `environment` array
2. Use placeholders if the values should be dynamic
3. Add corresponding workflow inputs if needed

Example:
```json
"environment": [
  {
    "name": "ENVIRONMENT",
    "value": "{{ENVIRONMENT}}"
  },
  {
    "name": "SPRING_PROFILES_ACTIVE",
    "value": "{{SPRING_PROFILE}}"
  }
]
```

## Output

After successful execution, the workflow provides:

- **Task Definition ARN**: The full ARN of the registered task definition
- **Revision Number**: The revision number assigned by ECS
- **Artifact**: A downloadable JSON file of the generated task definition

The workflow also generates a summary in the GitHub Actions UI with all the key information.

## Troubleshooting

### Authentication Errors

If you see authentication errors:
- Ensure `AWS_ACCOUNT_ID` is set in repository secrets
- Verify the IAM role exists and has correct trust relationships
- Check that the role has necessary permissions

### Invalid Task Definition

If task definition registration fails:
- Review the generated task definition in the workflow logs
- Verify all ARNs (IAM roles, secrets) are correct
- Ensure the task role and execution role exist

### Template Not Found

If the workflow can't find the template:
- Ensure `task-definition-template.json` is in the repository root
- Check the file path in the workflow matches the actual location
