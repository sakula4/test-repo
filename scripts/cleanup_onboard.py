#!/usr/bin/env python3
"""
Cleanup Onboarding Workflow Script

This script deletes the temporary onboarding workflow file after successful tenant deployment
and commits the changes to the specified branch.

Usage:
    python cleanup_onboard.py <branch_name>

Requirements:
    - GitPython: pip install GitPython
    - PyGithub: pip install PyGithub
"""

import os
import sys
import argparse
from pathlib import Path
from git import Repo, GitCommandError
from github import Github, Auth
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OnboardingCleanup:
    def __init__(self, branch_name, repo_path=None):
        """Initialize the cleanup manager.
        
        Args:
            branch_name (str): Name of the branch to work on
            repo_path (str, optional): Path to the repository. Defaults to current directory.
        """
        self.branch_name = branch_name
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        
        # Initialize Git repository
        try:
            self.git_repo = Repo(self.repo_path)
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            raise
            
        # Define file paths
        self.onboarding_file = self.repo_path / '.github' / 'workflows' / 'onboarding_workflow.yml'
        
        # GitHub configuration
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            auth = Auth.Token(github_token)
            self.github_client = Github(auth=auth)
            # Extract repository info from remote URL
            try:
                remote_url = self.git_repo.remote('origin').url
                if 'github.com' in remote_url:
                    # Parse repository name from URL
                    if remote_url.endswith('.git'):
                        remote_url = remote_url[:-4]
                    repo_parts = remote_url.split('/')[-2:]
                    self.github_repository = f"{repo_parts[0]}/{repo_parts[1]}"
                    self.repo = self.github_client.get_repo(self.github_repository)
                    logger.info(f"Connected to GitHub repository: {self.github_repository}")
                else:
                    logger.warning("Not a GitHub repository, GitHub operations disabled")
                    self.github_client = None
            except Exception as e:
                logger.warning(f"Could not connect to GitHub: {e}")
                self.github_client = None
        else:
            logger.warning("GITHUB_TOKEN not found, GitHub operations disabled")
            self.github_client = None

    def check_branch_exists(self):
        """Check if the specified branch exists locally or remotely."""
        try:
            # Check if branch exists locally
            if self.branch_name in [head.name for head in self.git_repo.heads]:
                logger.info(f"Branch '{self.branch_name}' found locally")
                return True
            
            # Check if branch exists remotely
            try:
                self.git_repo.remotes.origin.fetch()
                remote_branches = [ref.name for ref in self.git_repo.remotes.origin.refs]
                remote_branch_name = f"origin/{self.branch_name}"
                
                if remote_branch_name in remote_branches:
                    logger.info(f"Branch '{self.branch_name}' found remotely")
                    return True
            except Exception as e:
                logger.warning(f"Could not fetch remote branches: {e}")
            
            logger.error(f"Branch '{self.branch_name}' not found locally or remotely")
            return False
            
        except Exception as e:
            logger.error(f"Error checking branch existence: {e}")
            return False

    def checkout_branch(self):
        """Checkout the specified branch."""
        try:
            # If branch exists locally, check it out
            if self.branch_name in [head.name for head in self.git_repo.heads]:
                self.git_repo.git.checkout(self.branch_name)
                logger.info(f"Checked out local branch: {self.branch_name}")
                return True
            
            # If branch exists remotely, create local tracking branch
            try:
                self.git_repo.remotes.origin.fetch()
                remote_branch = f"origin/{self.branch_name}"
                
                # Create and checkout local tracking branch
                new_branch = self.git_repo.create_head(self.branch_name, remote_branch)
                new_branch.set_tracking_branch(self.git_repo.remotes.origin.refs[self.branch_name])
                new_branch.checkout()
                logger.info(f"Created and checked out tracking branch: {self.branch_name}")
                return True
                
            except Exception as e:
                logger.error(f"Could not create tracking branch: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking out branch: {e}")
            return False

    def delete_onboarding_file(self):
        """Delete the onboarding workflow file if it exists."""
        try:
            if self.onboarding_file.exists():
                # Remove the file
                self.onboarding_file.unlink()
                logger.info(f"Deleted onboarding workflow file: {self.onboarding_file}")
                
                # Stage the deletion
                self.git_repo.index.remove([str(self.onboarding_file)], working_tree=True)
                logger.info("Staged file deletion")
                return True
            else:
                logger.warning(f"Onboarding workflow file not found: {self.onboarding_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting onboarding file: {e}")
            return False

    def commit_changes(self):
        """Commit the changes to the current branch."""
        try:
            # Check if there are changes to commit
            if not self.git_repo.is_dirty() and not self.git_repo.untracked_files:
                logger.warning("No changes to commit")
                return False
            
            # Create commit
            commit_message = f"""🗑️ Cleanup: Remove temporary onboarding workflow

- Deleted .github/workflows/onboarding_workflow.yml
- Onboarding process completed successfully
- Regular GitOps workflow is now active

Branch: {self.branch_name}
"""
            
            commit = self.git_repo.index.commit(commit_message)
            logger.info(f"Committed changes: {commit.hexsha[:8]}")
            logger.info(f"Commit message: {commit_message.strip()}")
            return True
            
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return False

    def push_changes(self):
        """Push the changes to the remote repository."""
        try:
            # Push to remote
            origin = self.git_repo.remote('origin')
            push_info = origin.push(self.branch_name)
            
            if push_info and push_info[0].flags == push_info[0].flags.UP_TO_DATE:
                logger.info("Remote is already up to date")
            elif push_info and push_info[0].flags == push_info[0].flags.FAST_FORWARD:
                logger.info(f"Successfully pushed changes to remote branch: {self.branch_name}")
            else:
                logger.info(f"Push completed with flags: {push_info[0].flags if push_info else 'unknown'}")
            
            return True
            
        except GitCommandError as e:
            logger.error(f"Git push failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return False

    def add_cleanup_comment(self):
        """Add a comment to the PR indicating cleanup completion."""
        if not self.github_client:
            logger.warning("GitHub client not available, skipping PR comment")
            return False
            
        try:
            # Find open PR for this branch
            pulls = self.repo.get_pulls(state='open', head=f"{self.repo.owner.login}:{self.branch_name}")
            
            if pulls.totalCount == 0:
                logger.warning(f"No open PR found for branch: {self.branch_name}")
                return False
            
            pr = pulls[0]
            comment_body = f"""## 🗑️ Onboarding Cleanup Completed

✅ **Temporary onboarding workflow removed successfully**

### Changes Made:
- 🗑️ Deleted `.github/workflows/onboarding_workflow.yml`
- ✅ Committed cleanup changes to branch: `{self.branch_name}`

### Status:
- 🎉 **Tenant onboarding process completed**
- 🔄 **Regular GitOps workflow now active**
- 📦 **Ready for production deployments**

### Next Steps:
1. **Merge this PR** to finalize the tenant setup
2. **Future deployments** will use the standard GitOps process:
   - Push to main → Dev deployment
   - Tags (v*.*.*)  → Stage/UAT/Prod deployments

---
*Cleanup performed automatically by onboarding cleanup script*
"""
            
            pr.create_issue_comment(comment_body)
            logger.info(f"Added cleanup comment to PR #{pr.number}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding PR comment: {e}")
            return False

    def cleanup(self):
        """Execute the complete cleanup process."""
        logger.info("🚀 Starting onboarding cleanup process...")
        logger.info(f"Target branch: {self.branch_name}")
        logger.info(f"Repository path: {self.repo_path}")
        
        # Step 1: Check if branch exists
        if not self.check_branch_exists():
            logger.error("❌ Branch check failed")
            return False
        
        # Step 2: Checkout the branch
        if not self.checkout_branch():
            logger.error("❌ Branch checkout failed")
            return False
        
        # Step 3: Delete the onboarding file
        file_deleted = self.delete_onboarding_file()
        if not file_deleted:
            logger.warning("⚠️ No onboarding file to delete")
        
        # Step 4: Commit changes (only if file was deleted)
        if file_deleted:
            if not self.commit_changes():
                logger.error("❌ Commit failed")
                return False
            
            # Step 5: Push changes
            if not self.push_changes():
                logger.error("❌ Push failed")
                return False
        
        # Step 6: Add PR comment
        self.add_cleanup_comment()
        
        logger.info("✅ Onboarding cleanup completed successfully!")
        return True

def main():
    """Main function to run the cleanup script."""
    parser = argparse.ArgumentParser(
        description='Cleanup temporary onboarding workflow after successful tenant deployment'
    )
    parser.add_argument(
        'branch_name',
        help='Name of the branch containing the onboarding workflow to cleanup'
    )
    parser.add_argument(
        '--repo-path',
        default=None,
        help='Path to the repository (defaults to current directory)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize cleanup manager
        cleanup_manager = OnboardingCleanup(
            branch_name=args.branch_name,
            repo_path=args.repo_path
        )
        
        # Execute cleanup
        success = cleanup_manager.cleanup()
        
        if success:
            print(f"✅ Successfully cleaned up onboarding workflow for branch: {args.branch_name}")
            sys.exit(0)
        else:
            print(f"❌ Cleanup failed for branch: {args.branch_name}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Cleanup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
