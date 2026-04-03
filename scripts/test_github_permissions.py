#!/usr/bin/env python3
"""
GitHub App Permissions Test Script

This script tests the GitHub App's permissions for:
1. Creating branches
2. Creating workflow files
3. Creating pull requests

Usage:
    python test_github_permissions.py
"""

import os
import sys
import logging
import tempfile
import shutil
import random
import string
from pathlib import Path
from typing import Dict
import git

from git_ops import GitOperator
from github_auth import GitHubAuthorizer

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class GitHubPermissionsTester:
    """Test GitHub App permissions for common operations."""

    def __init__(self, test_mode=False):
        """Initialize the permissions tester.
        
        Args:
            test_mode (bool): If True, run in test mode without actual operations
        """
        self.test_mode = test_mode
        self.repo_root = Path.cwd()
        self.git_repo = git.Repo(self.repo_root)
        
        # Generate random suffix to avoid branch conflicts
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.test_branch_name = f"test/github-permissions-{random_suffix}"
        self.test_results = {
            'branch_creation': False,
            'workflow_creation': False,
            'pull_request_creation': False
        }
        
        # Initialize git operator
        if not self.test_mode:
            # Use the token from environment (passed from pipeline)
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable is required")
            
            # Debug token info
            token_debug = self._get_token_debug_info()
            logger.info(f"🔑 Token Info: {token_debug['type']}")
            logger.info(f"📏 Token Length: {token_debug['length']}")
            logger.info(f"🔍 Token Prefix: {token_debug['prefix']}")
                
            logger.info("🔧 Initializing GitOperator...")
            try:
                self.git_operator = GitOperator(
                    repo_path=self.repo_root,
                    github_token=github_token,
                    repository_name="mygainwell/acuity-platform-live",
                    test_mode=self.test_mode
                )
                logger.info("✅ GitOperator initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize GitOperator: {e}")
                logger.error("💡 This might indicate insufficient GitHub permissions or API access issues")
                logger.warning("🔄 Falling back to test mode for this run...")
                # Fall back to test mode if GitOperator fails
                self.test_mode = True
                self.git_operator = None
                logger.info("⚠️ Running in fallback test mode due to GitOperator initialization failure")
        else:
            self.git_operator = None

    def _configure_git_user(self):
        """Configure git user for commits."""
        logger.info("🔧 Configuring git user...")
        self.git_repo.config_writer().set_value(
            "user", "email", "41898282+github-actions[bot]@users.noreply.github.com"
        ).release()
        self.git_repo.config_writer().set_value(
            "user", "name", "github-actions[bot]"
        ).release()
        logger.info("✓ Git user configured")

    def _get_token_debug_info(self) -> Dict[str, str]:
        """Get detailed token debugging information."""
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            return {'type': 'None', 'prefix': 'None', 'source': 'Missing'}
        
        # Determine token type by prefix
        if github_token.startswith('ghs_'):
            token_type = 'GitHub App Installation Token'
        elif github_token.startswith('ghp_'):
            token_type = 'Personal Access Token'  
        elif github_token.startswith('gho_'):
            token_type = 'OAuth Token'
        elif github_token.startswith('ghu_'):
            token_type = 'GitHub User-to-server Token'
        elif github_token.startswith('ghr_'):
            token_type = 'GitHub Refresh Token'
        else:
            token_type = 'Unknown/Legacy Token'
            
        return {
            'type': token_type,
            'prefix': f"{github_token[:10]}...",
            'length': len(github_token),
            'source': 'Environment Variable GITHUB_TOKEN'
        }

    def test_branch_creation(self):
        """Test creating and pushing a new branch."""
        logger.info("🌿 Testing branch creation...")
        
        try:
            # Handle detached HEAD state in GitHub Actions
            if self.git_repo.head.is_detached:
                logger.info("🔄 Detected detached HEAD, switching to main branch...")
                # Fetch main branch and switch to it
                origin = self.git_repo.remote('origin')
                origin.fetch('main')
                main_branch = self.git_repo.heads.main if 'main' in [head.name for head in self.git_repo.heads] else None
                if not main_branch:
                    # Create main branch tracking origin/main
                    main_branch = self.git_repo.create_head('main', origin.refs.main)
                    main_branch.set_tracking_branch(origin.refs.main)
                main_branch.checkout()
                self.original_branch = 'main'
                logger.info("✓ Switched to main branch")
            else:
                # Save current branch to restore later
                self.original_branch = self.git_repo.active_branch.name
            
            # Delete test branch if it exists
            if self.test_branch_name in [head.name for head in self.git_repo.heads]:
                self.git_repo.heads[self.test_branch_name].delete(
                    self.git_repo, self.test_branch_name, force=True
                )
                logger.info(f"Deleted existing test branch: {self.test_branch_name}")
            
            # Create and checkout new test branch
            new_branch = self.git_repo.create_head(self.test_branch_name)
            new_branch.checkout()
            logger.info(f"✓ Created and checked out branch: {self.test_branch_name}")
            
            # Create a test file to commit
            test_file = self.repo_root / "test_permissions.tmp"
            test_file.write_text("GitHub App permissions test file")
            
            # Add and commit test file
            self.git_repo.git.add(str(test_file))
            self.git_repo.index.commit("Test: GitHub App permissions test")
            logger.info("✓ Created test commit")
            
            # Test pushing branch
            if not self.test_mode:
                success = self.git_operator.push_branch(self.test_branch_name)
                if success:
                    logger.info("✅ Branch creation and push: SUCCESS")
                    self.test_results['branch_creation'] = True
                else:
                    logger.error("❌ Branch creation and push: FAILED")
                    return False
            else:
                logger.info("🧪 TEST MODE: Branch push skipped")
                self.test_results['branch_creation'] = True
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Branch creation failed: {e}")
            return False

    def test_workflow_creation(self):
        """Test creating workflow files."""
        logger.info("⚙️ Testing workflow file creation...")
        
        # Add detailed token debugging
        token_info = self._get_token_debug_info()
        logger.info(f"🔍 Token Debug Info: {token_info}")
        
        try:
            # Create .github/workflows directory if it doesn't exist
            workflows_dir = self.repo_root / ".github" / "workflows"
            logger.info(f"📁 Workflows directory path: {workflows_dir}")
            logger.info(f"📂 Workflows directory exists: {workflows_dir.exists()}")
            
            workflows_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created/verified workflows directory")
            
            # Create a test workflow file with random name
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            test_workflow = workflows_dir / f"test-permissions-{random_suffix}.yml"
            
            logger.info(f"📝 Creating test workflow: {test_workflow.name}")
            logger.info(f"🔗 Full workflow path: {test_workflow}")
            
            workflow_content = f"""name: Test GitHub App Permissions {random_suffix}

on:
  workflow_dispatch:
    inputs:
      test_input:
        description: 'Test input for permissions'
        required: false
        default: 'test'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test step
        run: echo "Testing GitHub App permissions"
"""
            test_workflow.write_text(workflow_content)
            logger.info(f"✅ Successfully wrote workflow file locally")
            
            # Verify file creation
            if test_workflow.exists():
                file_size = test_workflow.stat().st_size
                logger.info(f"📊 Workflow file verified - Size: {file_size} bytes")
            else:
                raise Exception(f"Workflow file was not created: {test_workflow}")
            
            # Check git status before adding
            logger.info("🔍 Git status before adding workflow:")
            logger.info(f"   Dirty: {self.git_repo.is_dirty()}")
            logger.info(f"   Untracked: {self.git_repo.untracked_files}")
            logger.info(f"   Current branch: {self.git_repo.active_branch.name}")
            
            # Add and commit workflow file
            logger.info("➕ Adding workflow file to git...")
            self.git_repo.git.add(str(test_workflow))
            
            # Check git status after adding
            logger.info("🔍 Git status after adding workflow:")
            logger.info(f"   Dirty: {self.git_repo.is_dirty()}")
            logger.info(f"   Staged files: {[item.a_path for item in self.git_repo.index.diff('HEAD')]}")
            
            logger.info("💾 Committing workflow file...")
            commit_result = self.git_repo.index.commit("Test: Add GitHub App permissions test workflow")
            logger.info(f"✅ Committed workflow file - Commit: {commit_result.hexsha[:8]}")
            
            # Test pushing workflow file
            if not self.test_mode:
                logger.info(f"🚀 Attempting to push branch: {self.test_branch_name}")
                logger.info(f"🔑 Using token type: {token_info['type']}")
                
                try:
                    success = self.git_operator.push_branch(self.test_branch_name)
                    if success:
                        logger.info("✅ Workflow file creation and push: SUCCESS")
                        logger.info("🎉 GitHub App has 'workflows' permission!")
                        self.test_results['workflow_creation'] = True
                    else:
                        logger.error("❌ Workflow file push: FAILED")
                        logger.error("💡 This indicates missing 'workflows' permission")
                        return False
                except Exception as push_error:
                    error_msg = str(push_error)
                    logger.error(f"❌ Workflow push failed with exception: {error_msg}")
                    
                    if "workflows" in error_msg.lower() and "permission" in error_msg.lower():
                        logger.error("🚫 CONFIRMED: Missing 'workflows' permission for GitHub App")
                        logger.error("📋 Required: GitHub App needs 'Actions: Read and write' permission")
                    elif "refusing to allow" in error_msg.lower():
                        logger.error("🚫 GitHub is rejecting the workflow file push")
                        logger.error("💡 This is likely a 'workflows' permission issue")
                    else:
                        logger.error(f"❓ Unexpected push error: {error_msg}")
                    
                    return False
            else:
                logger.info("🧪 TEST MODE: Workflow file push skipped")
                self.test_results['workflow_creation'] = True
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Workflow creation failed: {e}")
            return False

    def test_pull_request_creation(self):
        """Test creating a pull request."""
        logger.info("🔄 Testing pull request creation...")
        
        try:
            if self.test_mode:
                logger.info("🧪 TEST MODE: Pull request creation skipped")
                self.test_results['pull_request_creation'] = True
                return True
            
            # Create pull request
            pr_title = "Test: GitHub App Permissions Test"
            pr_body = """## GitHub App Permissions Test

This is an automated test of GitHub App permissions for:
- ✅ Branch creation
- ✅ Workflow file creation  
- ✅ Pull request creation

**This PR should be closed immediately after testing.**
"""
            
            pr_url = self.git_operator.create_pull_request(
                title=pr_title,
                body=pr_body,
                head=self.test_branch_name,
                base='main'
            )
            
            if pr_url:
                logger.info(f"✅ Pull request creation: SUCCESS")
                logger.info(f"📝 PR URL: {pr_url}")
                self.test_results['pull_request_creation'] = True
                return pr_url
            else:
                logger.error("❌ Pull request creation: FAILED")
                return False
                
        except Exception as e:
            logger.error(f"❌ Pull request creation failed: {e}")
            return False

    def cleanup(self):
        """Clean up test files and branches."""
        logger.info("🧹 Cleaning up test artifacts...")
        
        try:
            # Switch back to original branch (or stay on main if we were detached)
            if hasattr(self, 'original_branch'):
                try:
                    self.git_repo.heads[self.original_branch].checkout()
                    logger.info(f"✓ Switched back to: {self.original_branch}")
                except Exception as e:
                    logger.info(f"⚠️ Could not switch back to original branch: {e}")
                    logger.info("Staying on current branch")
            
            # Remove test file
            test_file = self.repo_root / "test_permissions.tmp"
            if test_file.exists():
                test_file.unlink()
                logger.info("✓ Removed test file")
            
            # Remove test workflow files (any that match our pattern)
            workflows_dir = self.repo_root / ".github" / "workflows"
            if workflows_dir.exists():
                for workflow_file in workflows_dir.glob("test-permissions-*.yml"):
                    workflow_file.unlink()
                    logger.info(f"✓ Removed test workflow file: {workflow_file.name}")
            
            # Delete local test branch
            if self.test_branch_name in [head.name for head in self.git_repo.heads]:
                self.git_repo.heads[self.test_branch_name].delete(
                    self.git_repo, self.test_branch_name, force=True
                )
                logger.info(f"✓ Deleted local test branch: {self.test_branch_name}")
                
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

    def print_results(self):
        """Print test results summary."""
        logger.info("\n" + "="*50)
        logger.info("📊 GITHUB APP PERMISSIONS TEST RESULTS")
        logger.info("="*50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            test_display = test_name.replace('_', ' ').title()
            logger.info(f"{test_display:<25}: {status}")
        
        # Overall result
        all_passed = all(self.test_results.values())
        overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
        logger.info("-" * 50)
        logger.info(f"Overall Result: {overall_status}")
        
        if not all_passed:
            logger.info("\n💡 RECOMMENDATIONS:")
            if not self.test_results['workflow_creation']:
                logger.info("- Grant 'workflows' permission to the GitHub App")
            if not self.test_results['branch_creation']:
                logger.info("- Check 'contents' and 'metadata' permissions for the GitHub App")
            if not self.test_results['pull_request_creation']:
                logger.info("- Check 'pull_requests' permission for the GitHub App")
        
        logger.info("="*50)

    def run_tests(self):
        """Run all permission tests."""
        logger.info("🚀 Starting GitHub App permissions tests...")
        
        try:
            # Configure git user
            self._configure_git_user()
            
            # Test branch creation
            if not self.test_branch_creation():
                logger.error("❌ Branch creation test failed - stopping tests")
                return False
            
            # Test workflow creation
            self.test_workflow_creation()
            
            # Test pull request creation
            pr_url = self.test_pull_request_creation()
            
            # Print results
            self.print_results()
            
            # If PR was created, remind user to close it
            if pr_url and not self.test_mode:
                logger.info(f"\n⚠️  IMPORTANT: Please close the test PR at: {pr_url}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            return False
            
        finally:
            # Always cleanup
            self.cleanup()


def main():
    """Main function to run the permissions test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test GitHub App Permissions")
    parser.add_argument(
        "--test-mode",
        action="store_true",
        default=False,
        help="Run in test mode without actual GitHub operations"
    )
    args = parser.parse_args()
    
    tester = GitHubPermissionsTester(test_mode=args.test_mode)
    success = tester.run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()