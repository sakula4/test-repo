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
from github import Github
import git


class TenantCreator:
    def __init__(self):
        """Initialize the TenantCreator with environment variables."""
        self.tenant_name = os.getenv('TENANT_NAME')
        self.sub_tenant_name = os.getenv('SUB_TENANT_NAME')
        self.dev_network_range = os.getenv('DEV_NETWORK_RANGE')
        self.stage_network_range = os.getenv('STAGE_NETWORK_RANGE')
        self.enable_departure = os.getenv('ENABLE_DEPARTURE', 'false').lower() == 'true'
        self.enable_avscan = os.getenv('ENABLE_AVSCAN', 'false').lower() == 'true'
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repository = os.getenv('GITHUB_REPOSITORY')
        
        # Validate required inputs
        if not all([self.tenant_name, self.sub_tenant_name, self.dev_network_range, 
                   self.stage_network_range, self.github_token]):
            print("Error: Missing required environment variables")
            sys.exit(1)
        
        self.repo_root = Path.cwd()
        self.template_tenant_dir = self.repo_root / 'template-repo' / 'tenant'
        self.template_workflows_dir = self.repo_root / 'template-repo' / 'workflows'
        self.tenant_dir = self.repo_root / 'tenant' / self.tenant_name
        self.workflows_dir = self.repo_root / '.github' / 'workflows'
        
        # Initialize GitHub API
        self.gh = Github(self.github_token)
        self.repo = self.gh.get_repo(self.github_repository)
        
        # Initialize Git
        self.git_repo = git.Repo(self.repo_root)

    def print_inputs(self):
        """Print all input values."""
        print("=== Tenant Creation Inputs ===")
        print(f"Tenant Name: {self.tenant_name}")
        print(f"Sub-Tenant Name: {self.sub_tenant_name}")
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
        
        # Copy workflow files with placeholder replacement
        if self.template_workflows_dir.exists():
            for item in self.template_workflows_dir.iterdir():
                if item.is_file():
                    # Replace {{name}} with tenant_name in filename
                    dest_filename = item.name.replace('{{name}}', self.tenant_name)
                    dest = self.workflows_dir / dest_filename
                    self._copy_and_replace_placeholders(item, dest)
                    print(f"Copied and processed workflow file: {dest_filename}")
        else:
            print(f"Warning: Template workflows directory {self.template_workflows_dir} does not exist")

    def _copy_and_replace_placeholders(self, source_file, dest_file):
        """Copy a file and replace placeholder values."""
        try:
            # Read the source file
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace placeholders
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

    def _replace_placeholders(self, content):
        """Replace placeholder values in content with actual values."""
        placeholders = {
            '{{tenant_name}}': self.tenant_name,
            '{{name}}': self.tenant_name,
            '{{sub_tenant_name}}': self.sub_tenant_name,
            '{{dev_network_range}}': self.dev_network_range,
            '{{stage_network_range}}': self.stage_network_range,
            '{{enable_departure}}': str(self.enable_departure).lower(),
            '{{enable_avscan}}': str(self.enable_avscan).lower(),
            '{{TENANT_NAME}}': self.tenant_name.upper(),
            '{{SUB_TENANT_NAME}}': self.sub_tenant_name.upper(),
            '{{DEV_NETWORK_RANGE}}': self.dev_network_range,
            '{{STAGE_NETWORK_RANGE}}': self.stage_network_range,
            '{{ENABLE_DEPARTURE}}': str(self.enable_departure).upper(),
            '{{ENABLE_AVSCAN}}': str(self.enable_avscan).upper()
        }
        
        # Replace all placeholders
        for placeholder, value in placeholders.items():
            content = content.replace(placeholder, value)
        
        return content

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
- Sub-Tenant: {self.sub_tenant_name}
- Dev Network: {self.dev_network_range}
- Stage Network: {self.stage_network_range}
- Departure Enabled: {self.enable_departure}
- AVScan Enabled: {self.enable_avscan}

Generated from templates:
- Copied tenant config from template-repo/tenant/
- Copied workflows from template-repo/workflows/
- Replaced all placeholder values with actual inputs
"""
            
            # Commit changes
            self.git_repo.index.commit(commit_message)
            print("Changes committed locally")
            
            # Push to remote
            origin = self.git_repo.remote('origin')
            origin.push(refspec=f'{self.branch_name}:{self.branch_name}')
            print(f"Pushed branch {self.branch_name} to remote")
            
        except Exception as e:
            print(f"Error committing and pushing changes: {e}")
            sys.exit(1)

    def create_pull_request(self):
        """Create a pull request for the new tenant."""
        try:
            pr_title = f"Add tenant: {self.tenant_name}"
            pr_body = f"""## New Tenant Creation

**Tenant Details:**
- **Tenant Name:** {self.tenant_name}
- **Sub-Tenant Name:** {self.sub_tenant_name}
- **Development Network Range:** {self.dev_network_range}
- **Stage Network Range:** {self.stage_network_range}
- **Enable Departure:** {self.enable_departure}
- **Enable AVScan:** {self.enable_avscan}

**Changes Made:**
- ✅ Copied tenant configuration from `template-repo/tenant/` to `tenant/{self.tenant_name}/`
- ✅ Generated workflow from template: `tenant_{self.tenant_name}.yml`
- ✅ Generated deployment workflow from template: `tenant_{self.tenant_name}_deploy.yml`
- ✅ Replaced all placeholder values with actual tenant inputs

**Next Steps:**
1. Review the tenant configuration files
2. Validate network range assignments
3. Test the workflows
4. Merge when ready

---
*This PR was automatically created by the tenant creation workflow.*
"""
            
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=self.branch_name,
                base="main"
            )
            
            print(f"Pull request created: {pr.html_url}")
            return pr.html_url
            
        except Exception as e:
            print(f"Error creating pull request: {e}")
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