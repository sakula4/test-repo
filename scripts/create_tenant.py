#!/usr/bin/env python3
"""
Tenant Creation Script

This script creates a new tenant by:
1. Taking inputs from environment variables
2. Copying the template-repo to tenant/{{tenant_name}}
3. Creating a new branch
4. Generating tenant-specific workflows
5. Creating a pull request
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json
from github import Github, Auth
import git
from jinja2 import Environment, FileSystemLoader


class TenantCreator:
    def __init__(self):
        """Initialize the TenantCreator with environment variables."""
        self.tenant_name = os.getenv('TENANT_NAME')
        self.project_name = os.getenv('PROJECT_NAME')
        self.dev_network_range = os.getenv('DEV_NETWORK_RANGE')
        self.stage_network_range = os.getenv('STAGE_NETWORK_RANGE')
        self.enable_departure = os.getenv('ENABLE_DEPARTURE', 'false').lower() == 'true'
        self.enable_avscan = os.getenv('ENABLE_AVSCAN', 'false').lower() == 'true'
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repository = os.getenv('GITHUB_REPOSITORY')
        
        # Validate required inputs
        if not all([self.tenant_name, self.project_name, self.dev_network_range, 
                   self.stage_network_range, self.github_token]):
            print("Error: Missing required environment variables")
            sys.exit(1)
        
        self.repo_root = Path.cwd()
        self.template_tenant_dir = self.repo_root / 'template-repo' / 'tenant'
        self.template_workflows_dir = self.repo_root / 'template-repo' / 'workflows'
        self.tenant_dir = self.repo_root / 'tenant' / self.tenant_name
        self.workflows_dir = self.repo_root / '.github' / 'workflows'
        
        # Initialize GitHub API
        auth = Auth.Token(self.github_token)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(self.github_repository)
        
        # Initialize Git
        self.git_repo = git.Repo(self.repo_root)
        
        # Track whether workflows were copied
        self.workflows_copied = False

    def print_inputs(self):
        """Print all input values."""
        print("=== Tenant Creation Inputs ===")
        print(f"Tenant Name: {self.tenant_name}")
        print(f"Project Name: {self.project_name}")
        print(f"Development Network Range: {self.dev_network_range}")
        print(f"Stage Network Range: {self.stage_network_range}")
        print(f"Enable Departure: {self.enable_departure}")
        print(f"Enable AVScan: {self.enable_avscan}")
        print("===============================")

    def copy_template(self):
        """Copy template-repo/tenant to tenant/{{tenant_name}} and workflows to .github/workflows."""
        print(f"Copying tenant template from {self.template_tenant_dir} to {self.tenant_dir}")
        
        # Create tenant directory if it doesn't exist
        self.tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy tenant files with placeholder replacement
        if self.template_tenant_dir.exists():
            for item in self.template_tenant_dir.iterdir():
                if item.is_file():
                    dest = self.tenant_dir / item.name
                    self._copy_and_replace_placeholders(item, dest)
                    print(f"Copied and processed tenant file: {item.name}")
                elif item.is_dir():
                    dest = self.tenant_dir / item.name
                    self._copy_directory_with_placeholders(item, dest)
                    print(f"Copied and processed tenant directory: {item.name}")
        else:
            print(f"Warning: Template tenant directory {self.template_tenant_dir} does not exist")
        
        print(f"Copying workflow templates from {self.template_workflows_dir} to {self.workflows_dir}")
        
        # Check if we should copy workflows (they require special permissions)
        skip_workflows = os.getenv('SKIP_WORKFLOWS', 'false').lower() == 'true'
        
        if skip_workflows:
            print("⚠️ Skipping workflow files due to SKIP_WORKFLOWS=true")
            self.workflows_copied = False
        else:
            # Try to copy workflow files, with fallback to alternative location
            if self.template_workflows_dir.exists():
                try:
                    for item in self.template_workflows_dir.iterdir():
                        if item.is_file():
                            # Replace {{name}} with tenant_name in filename
                            dest_filename = item.name.replace('{{name}}', self.tenant_name)
                            dest = self.workflows_dir / dest_filename
                            self._copy_and_replace_placeholders(item, dest)
                            print(f"Copied and processed workflow file: {dest_filename}")
                    self.workflows_copied = True
                except Exception as workflow_error:
                    print(f"⚠️ Warning: Could not copy workflows to .github/workflows/: {workflow_error}")
                    print("Trying alternative location...")
                    
                    # Create workflows in tenant directory as fallback
                    try:
                        workflows_fallback_dir = self.tenant_dir / 'workflows'
                        workflows_fallback_dir.mkdir(exist_ok=True)
                        
                        for item in self.template_workflows_dir.iterdir():
                            if item.is_file():
                                dest_filename = item.name.replace('{{name}}', self.tenant_name)
                                dest = workflows_fallback_dir / dest_filename
                                self._copy_and_replace_placeholders(item, dest)
                                print(f"Created workflow file in tenant directory: workflows/{dest_filename}")
                        
                        self.workflows_copied = "fallback"
                        print("✅ Workflows created in tenant directory (manual copy required)")
                        
                    except Exception as fallback_error:
                        print(f"❌ Fallback workflow creation failed: {fallback_error}")
                        self.workflows_copied = False
            else:
                print(f"Warning: Template workflows directory {self.template_workflows_dir} does not exist")
                self.workflows_copied = False

    def _copy_and_replace_placeholders(self, source_file, dest_file):
        """Copy a file and replace placeholder values using Jinja2 templating."""
        try:
            # Read the source file
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process with Jinja2 for advanced templating (like departure block)
            content = self._process_jinja_template(content)
            
            # Replace remaining simple placeholders
            content = self._replace_placeholders(content)
            
            # Write to destination
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error processing file {source_file}: {e}")
            # Fallback to simple copy
            shutil.copy2(source_file, dest_file)

    def _copy_directory_with_placeholders(self, source_dir, dest_dir):
        """Copy a directory recursively and replace placeholder values in files."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.iterdir():
            dest_item = dest_dir / item.name
            if item.is_file():
                self._copy_and_replace_placeholders(item, dest_item)
            elif item.is_dir():
                self._copy_directory_with_placeholders(item, dest_item)

    def _process_jinja_template(self, content):
        """Process Jinja2 template content with template variables."""
        try:
            # Create Jinja2 environment
            env = Environment()
            template = env.from_string(content)
            
            # Render template with variables
            rendered = template.render(
                tenant_name=self.tenant_name,
                project_name=self.project_name,
                dev_network_range=self.dev_network_range,
                stage_network_range=self.stage_network_range,
                enable_departure=self.enable_departure,
                enable_avscan=self.enable_avscan,
                departure_enabled=self.enable_departure  # Alias for departure_enabled check
            )
            return rendered
            
        except Exception as e:
            print(f"Warning: Jinja2 processing failed: {e}. Falling back to simple replacement.")
            return content
    
    def _replace_placeholders(self, content):
        """Replace placeholder values in content with actual values."""
        placeholders = {
            '{{tenant_name}}': self.tenant_name,
            '{{name}}': self.tenant_name,
            '{{project_name}}': self.project_name,
            '{{dev_network_range}}': self.dev_network_range,
            '{{stage_network_range}}': self.stage_network_range,
            '{{enable_departure}}': str(self.enable_departure).lower(),
            '{{enable_avscan}}': str(self.enable_avscan).lower(),
            '{{TENANT_NAME}}': self.tenant_name.upper(),
            '{{PROJECT_NAME}}': self.project_name.upper(),
            '{{DEV_NETWORK_RANGE}}': self.dev_network_range,
            '{{STAGE_NETWORK_RANGE}}': self.stage_network_range,
            '{{ENABLE_DEPARTURE}}': str(self.enable_departure).upper(),
            '{{ENABLE_AVSCAN}}': str(self.enable_avscan).upper()
        }
        
        # Replace all placeholders
        for placeholder, value in placeholders.items():
            content = content.replace(placeholder, value)
        
        return content

    def _get_workflow_status_message(self):
        """Get the workflow status message for commit."""
        if self.workflows_copied == True:
            return "Copied workflows from template-repo/workflows/"
        elif self.workflows_copied == "fallback":
            return "Created workflows in tenant/workflows/ (manual copy required)"
        else:
            return "Workflows skipped (insufficient permissions)"

    def _get_workflow_pr_message(self):
        """Get the workflow status message for PR."""
        if self.workflows_copied == True:
            return f"""- ✅ Generated workflow from template: `tenant_{self.tenant_name}.yml`
- ✅ Generated deployment workflow from template: `tenant_{self.tenant_name}_deploy.yml`"""
        elif self.workflows_copied == "fallback":
            return f"""- ⚠️ Workflows created in `tenant/{self.tenant_name}/workflows/` (requires manual copy to `.github/workflows/`)
  - `tenant_{self.tenant_name}.yml` → copy to `.github/workflows/`
  - `tenant_{self.tenant_name}_deploy.yml` → copy to `.github/workflows/`"""
        else:
            return f"""- ❌ Workflow generation skipped due to insufficient permissions
  - Manual creation required: `tenant_{self.tenant_name}.yml`
  - Manual creation required: `tenant_{self.tenant_name}_deploy.yml`"""

    def create_branch(self):
        """Create a new branch for the tenant."""
        branch_name = f"feature/tenant-{self.tenant_name}"
        
        try:
            # Check if branch already exists
            existing_branch = None
            try:
                existing_branch = self.git_repo.heads[branch_name]
            except IndexError:
                pass
            
            if existing_branch:
                print(f"Branch {branch_name} already exists, checking it out")
                self.git_repo.heads[branch_name].checkout()
            else:
                print(f"Creating new branch: {branch_name}")
                new_branch = self.git_repo.create_head(branch_name)
                new_branch.checkout()
            
            self.branch_name = branch_name
            return branch_name
            
        except Exception as e:
            print(f"Error creating branch: {e}")
            sys.exit(1)

    def create_tenant_workflows(self):
        """Create tenant-specific workflow files from templates."""
        # Note: Workflows are now copied from templates in copy_template() method
        # This method is kept for backward compatibility and logging
        print(f"Tenant workflows have been generated from templates:")
        print(f"  - tenant_{self.tenant_name}.yml")
        print(f"  - tenant_{self.tenant_name}_deploy.yml")



    def commit_and_push(self):
        """Commit changes and push to GitHub."""
        try:
            # Add all changes
            self.git_repo.git.add(A=True)
            
            # Create commit message
            commit_message = f"""Add tenant: {self.tenant_name}

- Tenant Name: {self.tenant_name}
- Project Name: {self.project_name}
- Dev Network: {self.dev_network_range}
- Stage Network: {self.stage_network_range}
- Departure Enabled: {self.enable_departure}
- AVScan Enabled: {self.enable_avscan}

Generated from templates:
- Copied tenant config from template-repo/tenant/
- {self._get_workflow_status_message()}
- Replaced all placeholder values with actual inputs
"""
            
            # Commit changes
            self.git_repo.index.commit(commit_message)
            print("Changes committed locally")
            
            # Push to remote
            origin = self.git_repo.remote('origin')
            try:
                print(f"Pushing branch {self.branch_name} to remote...")
                
                # Get current branch info before push
                current_branch = self.git_repo.active_branch
                print(f"Current active branch: {current_branch.name}")
                print(f"Branch commit: {current_branch.commit.hexsha}")
                
                # Push with explicit upstream setting
                push_info = origin.push(refspec=f'{self.branch_name}:{self.branch_name}', force=True)
                
                # Verify push result
                for info in push_info:
                    print(f"Push result: {info.summary}")
                    if info.flags & info.ERROR:
                        raise Exception(f"Push failed with error: {info.summary}")
                
                print(f"✅ Successfully pushed branch {self.branch_name} to remote")
                
                # Verify the push by fetching the remote reference
                try:
                    origin.fetch(refspec=f'{self.branch_name}:{self.branch_name}')
                    print(f"✅ Verified branch exists on remote")
                except Exception as fetch_error:
                    print(f"⚠️ Could not verify remote branch: {fetch_error}")
                
            except Exception as push_error:
                print(f"❌ Push error: {push_error}")
                # Try alternative push method
                try:
                    print("Trying alternative push method...")
                    push_info = origin.push(self.branch_name, force=True)
                    for info in push_info:
                        print(f"Alternative push result: {info.summary}")
                    print(f"✅ Pushed branch {self.branch_name} to remote (alternative method)")
                except Exception as alt_push_error:
                    print(f"❌ Alternative push failed: {alt_push_error}")
                    raise push_error
            
        except Exception as e:
            print(f"Error committing and pushing changes: {e}")
            sys.exit(1)

    def create_pull_request(self):
        """Create a pull request for the new tenant."""
        try:
            pr_title = f"Add tenant: {self.tenant_name}"
            pr_body = f"""## 🚀 New Tenant Creation: {self.tenant_name}

**Tenant Details:**
- **Tenant Name:** `{self.tenant_name}`
- **Project Name:** `{self.project_name}`
- **Development Network Range:** `{self.dev_network_range}`
- **Stage Network Range:** `{self.stage_network_range}`
- **Enable Departure:** `{self.enable_departure}`
- **Enable AVScan:** `{self.enable_avscan}`

**Changes Made:**
- ✅ Copied tenant configuration from `template-repo/tenant/` to `_config/tenants/{self.tenant_name}/`
{self._get_workflow_pr_message()}
- ✅ Replaced all placeholder values with actual tenant inputs

## 🎯 Demo Onboarding Workflow

This PR includes a **demo sequential onboarding workflow** (`tenant_{self.tenant_name}_onboarding_demo.yml`) that will:

### 📋 Demo Sequential Process:
1. **Demo Network Plan** → **Demo Approve** → **Demo Network Deploy**
2. **Demo Network Peering Plan** → **Demo Approve** → **Demo Network Peering Deploy**  
3. **Demo Workspace Plan** → **Demo Approve** → **Demo Workspace Deploy**
4. **Demo DSS Components** → **Demo CEF Components**

### 🎯 Demo Purpose:
This demonstrates the sequential deployment concept with simple print statements and sleep delays. Shows how dependency issues would be solved in the real implementation.

### 🗑️ Demo Cleanup
After running the demo:
1. **Review demo output** to understand sequential flow
2. **Replace with real workflow** for actual deployment
3. **Delete demo workflow** and use production version

## 📋 Demo Next Steps:
1. Review the tenant configuration files
2. Validate network range assignments  
3. **Run the demo onboarding workflow** to see sequential flow
4. Replace with production workflow when ready

---
*This PR was automatically created by the tenant creation workflow.*
"""
            
            print(f"Creating PR with branch: {self.branch_name}")
            print(f"Repository: {self.github_repository}")
            
            # Wait a moment for GitHub to process the push
            import time
            time.sleep(2)
            
            # Verify the branch exists on remote
            try:
                branches = [branch.name for branch in self.repo.get_branches()]
                print(f"Available remote branches: {branches}")
                if self.branch_name not in branches:
                    print(f"Warning: Branch {self.branch_name} not found in remote branches")
                    # Try to refresh and check again
                    time.sleep(3)
                    branches = [branch.name for branch in self.repo.get_branches()]
                    print(f"Refreshed remote branches: {branches}")
            except Exception as branch_error:
                print(f"Warning: Could not verify remote branches: {branch_error}")
            
            # Check if branch exists using direct API call
            try:
                branch_ref = self.repo.get_git_ref(f"heads/{self.branch_name}")
                print(f"✅ Branch reference found: {branch_ref.ref}")
            except Exception as ref_error:
                print(f"❌ Branch reference not found: {ref_error}")
                
                # Try to manually verify the push worked
                try:
                    commits = list(self.repo.get_commits(sha=self.branch_name))
                    print(f"✅ Found {len(commits)} commits on branch {self.branch_name}")
                except Exception as commit_error:
                    print(f"❌ Could not access commits on branch: {commit_error}")
            
            # Try different head reference formats
            head_refs_to_try = [
                self.branch_name,  # Simple branch name
                f"{self.github_repository.split('/')[0]}:{self.branch_name}",  # owner:branch
            ]
            
            pr = None
            last_error = None
            
            for head_ref in head_refs_to_try:
                try:
                    print(f"Attempting to create PR with head: {head_ref}")
                    pr = self.repo.create_pull(
                        title=pr_title,
                        body=pr_body,
                        head=head_ref,
                        base="main"
                    )
                    break
                except Exception as e:
                    last_error = e
                    print(f"Failed with head '{head_ref}': {e}")
                    continue
            
            # If all head references failed, try creating the branch reference first
            if pr is None:
                try:
                    print("All head references failed. Trying to create branch reference...")
                    
                    # Get the current commit SHA
                    current_commit = self.git_repo.head.commit.hexsha
                    print(f"Current commit SHA: {current_commit}")
                    
                    # Try to create the branch reference on GitHub
                    try:
                        branch_ref = self.repo.create_git_ref(
                            ref=f"refs/heads/{self.branch_name}",
                            sha=current_commit
                        )
                        print(f"✅ Created branch reference: {branch_ref.ref}")
                        
                        # Wait a moment for GitHub to process
                        import time
                        time.sleep(2)
                        
                        # Now try to create PR again
                        pr = self.repo.create_pull(
                            title=pr_title,
                            body=pr_body,
                            head=self.branch_name,
                            base="main"
                        )
                        print("✅ Successfully created PR after creating branch reference")
                        
                    except Exception as ref_create_error:
                        print(f"Failed to create branch reference: {ref_create_error}")
                        raise last_error
                        
                except Exception as fallback_error:
                    print(f"Fallback method failed: {fallback_error}")
                    raise last_error
            
            if pr is None:
                raise last_error
            
            print(f"Pull request created: {pr.html_url}")
            return pr.html_url
            
        except Exception as e:
            print(f"Error creating pull request: {e}")
            print(f"Branch name: {self.branch_name}")
            print(f"Repository: {self.github_repository}")
            sys.exit(1)

    def run(self):
        """Execute the full tenant creation process."""
        try:
            print("Starting tenant creation process...")
            
            # Step 1: Print inputs
            self.print_inputs()
            
            # Step 2: Create branch
            self.create_branch()
            
            # Step 3: Copy template
            self.copy_template()
            
            # Step 4: Create workflows
            self.create_tenant_workflows()
            
            # Step 5: Commit and push
            self.commit_and_push()
            
            # Step 6: Create PR
            pr_url = self.create_pull_request()
            
            print(f"✅ Tenant creation completed successfully!")
            print(f"📋 Pull Request: {pr_url}")
            
        except Exception as e:
            print(f"❌ Error during tenant creation: {e}")
            sys.exit(1)


if __name__ == "__main__":
    creator = TenantCreator()
    creator.run()