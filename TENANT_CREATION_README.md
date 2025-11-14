# Tenant Creation System

This system automates the creation of new tenants in the acuity-platform-live infrastructure.

## Overview

The tenant creation system consists of:
1. **GitHub Workflow** (`tenant_creation.yml`) - Provides a UI for input collection
2. **Python Script** (`create_tenant.py`) - Handles the actual tenant creation logic
3. **Generated Workflows** - Tenant-specific CI/CD and deployment workflows

## Usage

### Via GitHub Actions (Recommended)

1. Navigate to the **Actions** tab in the GitHub repository
2. Select **"Tenant Creation Workflow"**
3. Click **"Run workflow"**
4. Fill in the required inputs:
   - **Tenant Name**: The primary tenant identifier
   - **Sub-Tenant Name**: The sub-tenant identifier
   - **Development Network Range**: Network CIDR for dev environment (e.g., `10.1.0.0/16`)
   - **Stage Network Range**: Network CIDR for stage environment (e.g., `10.2.0.0/16`)
   - **Enable Departure**: Check if departure functionality should be enabled
   - **Enable AVScan**: Check if AVScan functionality should be enabled
5. Click **"Run workflow"**

### Manual Execution

If you need to run the script manually:

```bash
# Set environment variables
export TENANT_NAME="example-tenant"
export SUB_TENANT_NAME="example-sub"
export DEV_NETWORK_RANGE="10.1.0.0/16"
export STAGE_NETWORK_RANGE="10.2.0.0/16"
export ENABLE_DEPARTURE="true"
export ENABLE_AVSCAN="false"
export GITHUB_TOKEN="your-github-token"
export GITHUB_REPOSITORY="owner/repo-name"

# Install dependencies
pip install -r requirements.txt

# Run the script
python scripts/create_tenant.py
```

## Template Structure

The system uses templates from `template-repo/` with placeholder replacement:

```
template-repo/
├── tenant/                     # Tenant configuration templates
│   ├── dev-us-east-1.yaml
│   ├── prod-us-east-1.yaml
│   ├── stg-us-east-1.yaml
│   └── uat-us-east-1.yaml
└── workflows/                  # Workflow templates
    ├── tenant_{{name}}.yml
    └── tenant_{{name}}_deploy.yml
```

## What Gets Created

When you run the tenant creation workflow, the following will be generated:

### 1. Tenant Directory Structure
```
tenant/
└── {tenant_name}/              # Copied from template-repo/tenant/
    ├── dev-us-east-1.yaml     # With placeholder values replaced
    ├── prod-us-east-1.yaml
    ├── stg-us-east-1.yaml
    └── uat-us-east-1.yaml
```

### 2. Workflow Files
- **`tenant_{tenant_name}.yml`** - CI/CD workflow (from template with placeholders replaced)
- **`tenant_{tenant_name}_deploy.yml`** - Deployment workflow (from template with placeholders replaced)

### 3. Git Branch and Pull Request
- Creates a new branch: `feature/tenant-{tenant_name}`
- Commits all changes to the branch
- Creates a pull request to merge into `main`

## Generated Workflows

### Tenant CI/CD Workflow
The `tenant_{tenant_name}.yml` workflow includes:
- **Validation**: Checks tenant configuration
- **Build**: Builds tenant resources
- **Test**: Runs tenant-specific tests
- **Triggers**: Runs on pushes/PRs affecting the tenant directory

### Tenant Deployment Workflow
The `tenant_{tenant_name}_deploy.yml` workflow includes:
- **Manual Trigger**: Workflow dispatch with environment selection
- **Environment Support**: Deploy to dev, stage, or prod
- **Dry Run Option**: Test deployments without making changes
- **Feature Toggles**: Respects departure and AVScan settings

## Placeholder Replacement

The system replaces the following placeholders in template files:

### Available Placeholders
- `{{tenant_name}}` / `{{name}}` - Tenant name (lowercase)
- `{{TENANT_NAME}}` - Tenant name (uppercase)
- `{{sub_tenant_name}}` - Sub-tenant name (lowercase)
- `{{SUB_TENANT_NAME}}` - Sub-tenant name (uppercase)
- `{{dev_network_range}}` / `{{DEV_NETWORK_RANGE}}` - Development network CIDR
- `{{stage_network_range}}` / `{{STAGE_NETWORK_RANGE}}` - Stage network CIDR
- `{{enable_departure}}` / `{{ENABLE_DEPARTURE}}` - Departure feature flag
- `{{enable_avscan}}` / `{{ENABLE_AVSCAN}}` - AVScan feature flag

### Example Template Usage
```yaml
# In template-repo/tenant/dev-us-east-1.yaml
tenant_name: "{{tenant_name}}"
sub_tenant: "{{sub_tenant_name}}"
network_range: "{{dev_network_range}}"
features:
  departure_enabled: {{enable_departure}}
  avscan_enabled: {{enable_avscan}}
```

## Configuration

### Network Ranges
- **Development**: Used for dev environment deployments
- **Stage**: Used for staging environment deployments
- **Production**: Configuration handled separately for security

### Feature Toggles
- **Enable Departure**: Enables departure-related functionality
- **Enable AVScan**: Enables antivirus scanning capabilities

## Security Notes

- The workflow uses `GITHUB_TOKEN` for authentication
- Requires `contents: write` and `pull-requests: write` permissions
- All sensitive operations are performed through the GitHub API
- Network ranges should follow your organization's IP allocation scheme

## Troubleshooting

### Common Issues

1. **Missing GitHub Token**: Ensure `GITHUB_TOKEN` is available in the workflow
2. **Branch Already Exists**: The script will checkout the existing branch
3. **Network Range Conflicts**: Verify network ranges don't overlap with existing tenants
4. **Permission Errors**: Check repository permissions for the service account

### Debug Mode

To run the script in debug mode, add debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When modifying the tenant creation system:

1. Test changes on a development branch first
2. Update this README if adding new features
3. Ensure backward compatibility with existing tenants
4. Update the workflow templates as needed

## Support

For issues with tenant creation:
1. Check the workflow logs in GitHub Actions
2. Verify input parameters are correct
3. Ensure network ranges don't conflict
4. Contact the platform team if issues persist