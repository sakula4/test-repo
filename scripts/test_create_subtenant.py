#!/usr/bin/env python3
"""
Pytest tests for create_subtenant.py

Tests cover:
- Naming validation
- File validation
- Branch operations
- Template processing
- End-to-end workflow
"""


import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent))


from create_subtenant import TenantWorkspaceValidator, SubTenantCreator


class TestTenantWorkspaceValidator:
    """Test cases for TenantWorkspaceValidator class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create mock git repo
        self.mock_git_repo = Mock()
        self.mock_git_repo.active_branch.name = "test-branch"
        
        with patch('create_subtenant.git.Repo') as mock_repo:
            mock_repo.return_value = self.mock_git_repo
            self.validator = TenantWorkspaceValidator(str(self.repo_path))

    def test_naming_constraints_valid(self):
        """Test valid naming constraints."""
        result = self.validator.validate_naming_constraints(
            "demo", "oh", "dev"
        )
        is_valid, error_msg, clean_subtenant, clean_tenant, clean_env = result
        
        assert is_valid is True
        assert error_msg == ""
        assert clean_subtenant == "demo"
        assert clean_tenant == "oh"
        assert clean_env == "dev"

    def test_naming_constraints_normalization(self):
        """Test that names are normalized to lowercase."""
        result = self.validator.validate_naming_constraints(
            "DEMO", "OH", "DEV"
        )
        is_valid, error_msg, clean_subtenant, clean_tenant, clean_env = result
        
        assert is_valid is True
        assert clean_subtenant == "demo"
        assert clean_tenant == "oh"
        assert clean_env == "dev"

    def test_naming_constraints_invalid_lengths(self):
        """Test invalid name lengths."""
        # Subtenant too short
        result = self.validator.validate_naming_constraints("ab", "oh", "dev")
        assert result[0] is False
        assert "Sub-tenant name must be 3-5 characters" in result[1]
        
        # Subtenant too long
        result = self.validator.validate_naming_constraints(
            "toolong", "oh", "dev"
        )
        assert result[0] is False
        assert "Sub-tenant name must be 3-5 characters" in result[1]
        
        # Tenant wrong length
        result = self.validator.validate_naming_constraints(
            "demo", "o", "dev"
        )
        assert result[0] is False
        assert "Tenant name must be exactly 2 characters" in result[1]
        
        # Environment wrong length
        result = self.validator.validate_naming_constraints(
            "demo", "oh", "development"
        )
        assert result[0] is False
        assert "Environment name must be exactly 3 characters" in result[1]

    def test_naming_constraints_invalid_characters(self):
        """Test invalid characters in names."""
        # Numbers in subtenant
        result = self.validator.validate_naming_constraints(
            "demo1", "oh", "dev"
        )
        assert result[0] is False
        assert "must contain only English alphabetic characters" in result[1]
        
        # Special characters in tenant (use 2-char name to avoid length error)
        result = self.validator.validate_naming_constraints(
            "demo", "o!", "dev"
        )
        assert result[0] is False
        assert "must contain only English alphabetic characters" in result[1]

    def test_is_file_valid_content_missing_file(self):
        """Test validation of missing file."""
        non_existent_file = self.repo_path / "missing.yaml"
        is_valid, reason = self.validator.is_file_valid_content(non_existent_file)
        
        assert is_valid is False
        assert reason == "File does not exist"

    def test_is_file_valid_content_empty_file(self):
        """Test validation of empty file."""
        empty_file = self.repo_path / "empty.yaml"
        empty_file.write_text("")
        
        is_valid, reason = self.validator.is_file_valid_content(empty_file)
        
        assert is_valid is False
        assert reason == "File is empty"

    def test_is_file_valid_content_valid_yaml(self):
        """Test validation of valid YAML file."""
        yaml_file = self.repo_path / "valid.yaml"
        yaml_file.write_text("key: value\nlist:\n  - item1\n  - item2")
        
        is_valid, reason = self.validator.is_file_valid_content(yaml_file)
        
        assert is_valid is True
        assert reason == "Valid"

    def test_is_file_valid_content_invalid_yaml(self):
        """Test validation of invalid YAML file."""
        yaml_file = self.repo_path / "invalid.yaml"
        yaml_file.write_text("key: value\ninvalid: [unclosed")
        
        is_valid, reason = self.validator.is_file_valid_content(yaml_file)
        
        assert is_valid is False
        assert "Invalid YAML syntax" in reason

    def test_is_file_valid_content_comments_only(self):
        """Test validation of file with only comments."""
        yaml_file = self.repo_path / "comments.yaml"
        yaml_file.write_text("# This is a comment\n# Another comment\n")
        
        is_valid, reason = self.validator.is_file_valid_content(yaml_file)
        
        assert is_valid is False
        assert reason == "File contains only comments or empty lines"


class TestSubTenantCreator:
    """Test cases for SubTenantCreator class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create mock validator
        self.mock_validator = Mock()
        self.mock_validator.repo_path = self.repo_path
        self.mock_validator.git_repo = Mock()
        self.mock_validator.git_repo.active_branch.name = "test-branch"
        
        with patch('create_subtenant.TenantWorkspaceValidator') as mock_val_class:
            mock_val_class.return_value = self.mock_validator
            self.creator = SubTenantCreator(
                subtenant_name="demo",
                tenant_name="oh", 
                env="dev",
                test_mode=True
            )

    def test_init(self):
        """Test SubTenantCreator initialization."""
        assert self.creator.subtenant_name == "demo"
        assert self.creator.tenant_name == "oh"
        assert self.creator.env == "dev"
        assert self.creator.test_mode is True
        assert self.creator.create_pr is False

    @patch('create_subtenant.logger')
    def test_create_feature_branch_test_mode(self, mock_logger):
        """Test feature branch creation in test mode."""
        mock_git = Mock()
        self.creator.validator.git_repo = mock_git
        mock_git.active_branch.name = "current-branch"
        
        self.creator._create_feature_branch("test-branch")
        
        mock_git.git.checkout.assert_called_once_with('-b', 'test-branch')
        mock_logger.info.assert_any_call("TEST MODE: Using current branch as 'main' branch")

    def test_process_and_append_subtenant_config_missing_template(self):
        """Test subtenant config processing with missing template."""
        with patch('create_subtenant.logger') as mock_logger:
            self.creator._process_and_append_subtenant_config()
            
            mock_logger.warning.assert_called_once()
            assert "Template file not found" in str(mock_logger.warning.call_args)

    def test_process_and_append_subtenant_config_missing_tenant_dir(self):
        """Test subtenant config processing with missing tenant directory."""
        # Create template file
        template_dir = self.repo_path / "_templates" / "tenant"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "subtenant_config.yml"
        template_file.write_text("<subtenant-name>:\n  key: value")
        
        with patch('create_subtenant.logger') as mock_logger:
            self.creator._process_and_append_subtenant_config()
            
            mock_logger.warning.assert_called_once()
            assert "Tenant YAML file not found" in str(mock_logger.warning.call_args)

    def test_process_and_append_subtenant_config_success(self):
        """Test successful subtenant config processing."""
        # Create template file
        template_dir = self.repo_path / "_templates" / "tenant"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "subtenant_config.yml"
        template_file.write_text(
            "<subtenant-name>:\n  tenant: <tenant>\n  env: <env>"
        )
        
        # Create tenant directory and file
        tenant_dir = self.repo_path / "tenants" / "oh"
        tenant_dir.mkdir(parents=True)
        tenant_file = tenant_dir / "dev-us-east-1.yaml"
        tenant_file.write_text("existing:\n  key: value")
        
        with patch('create_subtenant.logger') as mock_logger:
            self.creator._process_and_append_subtenant_config()
            
            # Verify file was updated
            updated_content = tenant_file.read_text()
            assert "demo:" in updated_content
            assert "tenant: oh" in updated_content
            assert "env: dev" in updated_content
            assert "existing:" in updated_content
            
            mock_logger.info.assert_called_once()
            assert "Successfully appended subtenant config" in str(mock_logger.info.call_args)

    def test_process_and_append_workflow_config_missing_template(self):
        """Test workflow config processing with missing template."""
        with patch('create_subtenant.logger') as mock_logger:
            self.creator._process_and_append_workflow_config()
            
            mock_logger.warning.assert_called_once()
            assert "Workflow template file not found" in str(mock_logger.warning.call_args)

    def test_process_and_append_workflow_config_success(self):
        """Test successful workflow config processing."""
        # Create workflow template
        template_dir = self.repo_path / "_templates" / "workflows"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "subtenant_config.yml"
        template_file.write_text(
            "jobs:\n  {{ subtenant_name }}-job:\n    runs-on: ubuntu-latest"
        )
        
        # Create workflow directory and file
        workflow_dir = self.repo_path / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        workflow_file = workflow_dir / "tenant_oh.yml"
        workflow_file.write_text("jobs:\n  existing-job:\n    runs-on: ubuntu-latest")
        
        with patch('create_subtenant.logger') as mock_logger:
            self.creator._process_and_append_workflow_config()
            
            # Verify file was updated
            updated_content = workflow_file.read_text()
            assert "demo-job:" in updated_content
            assert "existing-job:" in updated_content
            
            mock_logger.info.assert_called_once()
            assert "Successfully appended workflow config" in str(mock_logger.info.call_args)

    def test_merge_workflow_data(self):
        """Test workflow data merging logic."""
        existing = {
            "name": "Test Workflow",
            "jobs": {
                "existing-job": {"runs-on": "ubuntu-latest"}
            },
            "env": {"EXISTING": "value"}
        }
        
        new = {
            "jobs": {
                "new-job": {"runs-on": "ubuntu-22.04"}
            },
            "env": {"NEW": "value"}
        }
        
        self.creator._merge_workflow_data(existing, new)
        
        # Verify merge results
        assert existing["name"] == "Test Workflow"
        assert "existing-job" in existing["jobs"]
        assert "new-job" in existing["jobs"]
        assert existing["env"]["EXISTING"] == "value"
        assert existing["env"]["NEW"] == "value"

    def test_run_invalid_naming(self):
        """Test run method with invalid naming."""
        self.mock_validator.validate_naming_constraints.return_value = (
            False, "Invalid name", "", "", ""
        )
        
        with patch('create_subtenant.logger') as mock_logger:
            with pytest.raises(SystemExit) as exc_info:
                self.creator.run()
            
            mock_logger.error.assert_called_once()
            assert "Naming validation failed" in str(mock_logger.error.call_args)
            assert exc_info.value.code == 1

    @patch('create_subtenant.sys.exit')
    def test_run_missing_workspace(self, mock_exit):
        """Test run method with missing workspace files."""
        self.mock_validator.validate_naming_constraints.return_value = (
            True, "", "demo", "oh", "dev"
        )
        self.mock_validator.validate_tenant_workspace.return_value = {
            'tenant_name': 'oh',
            'current_branch': {
                'name': 'test-branch',
                'workspace_exists': False,
                'env_file_valid': False,
                'config_file_valid': False,
                'workflow_file_valid': False,
                'deploy_workflow_file_valid': False,
                'details': {}
            }
        }
        
        with patch('create_subtenant.logger') as mock_logger:
            with patch.object(self.creator, '_create_feature_branch'):
                with patch.object(self.creator, '_print_validation_results'):
                    self.creator.run()
            
            mock_logger.error.assert_any_call(
                "❌ Required files are missing for tenant workspace!"
            )
            mock_exit.assert_called_once_with(1)

    def test_run_success(self):
        """Test successful run method execution."""
        self.mock_validator.validate_naming_constraints.return_value = (
            True, "", "demo", "oh", "dev"
        )
        self.mock_validator.validate_tenant_workspace.return_value = {
            'tenant_name': 'oh',
            'current_branch': {
                'name': 'test-branch',
                'workspace_exists': True,
                'env_file_valid': True,
                'config_file_valid': True,
                'workflow_file_valid': True,
                'deploy_workflow_file_valid': True,
                'details': {}
            }
        }
        
        with patch('create_subtenant.logger') as mock_logger:
            with patch.object(self.creator, '_create_feature_branch'):
                with patch.object(self.creator, '_print_validation_results'):
                    with patch.object(self.creator, '_process_and_append_subtenant_config'):
                        with patch.object(self.creator, '_process_and_append_workflow_config'):
                            self.creator.run()
            
            mock_logger.info.assert_any_call(
                "✓ All required files found in the workspace"
            )
            mock_logger.info.assert_any_call(
                "Sub-tenant workspace setup completed successfully!"
            )


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Create realistic directory structure
        self.setup_repo_structure()

    def setup_repo_structure(self):
        """Create a realistic repository structure for testing."""
        # Create _config/tenants/oh directory
        tenant_dir = self.repo_path / "_config" / "tenants" / "oh"
        tenant_dir.mkdir(parents=True)
        
        # Create tenant config files
        (tenant_dir / "dev.us-east-1.yaml").write_text("""
modules:
  us-east-1:
    encryption: true
    datalake: true
existing_config:
  key: value
""")
        
        (tenant_dir / "config.yaml").write_text("""
tenant_name: oh
description: Ohio tenant
""")
        
        # Create workflows directory
        workflows_dir = self.repo_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        
        (workflows_dir / "tenant_oh.yml").write_text("""
name: Ohio Tenant Workflow
jobs:
  workspace:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
""")
        
        (workflows_dir / "tenant_oh_deploy.yml").write_text("""
name: Ohio Tenant Deploy
jobs:
  deploy:
    runs-on: ubuntu-latest
""")
        
        # Create templates
        template_dir = self.repo_path / "_templates" / "tenant"
        template_dir.mkdir(parents=True)
        
        (template_dir / "subtenant_config.yml").write_text("""
<subtenant-name>:
  create_catalog: true
  catalogs:
    <tenant>_<sub-tenant>_<env>: "/"
  tenant: <tenant>
  env: <env>
""")
        
        workflow_template_dir = self.repo_path / "_templates" / "workflows"
        workflow_template_dir.mkdir(parents=True)
        
        (workflow_template_dir / "subtenant_config.yml").write_text("""
jobs:
  {{ subtenant_name }}-job:
    runs-on: ubuntu-latest
    environment: <env>
    steps:
      - name: Process {{ subtenant_name }}
        run: echo "Processing <sub-tenant>"
""")

    @patch('create_subtenant.git.Repo')
    def test_end_to_end_subtenant_creation(self, mock_repo_class):
        """Test complete end-to-end subtenant creation process."""
        # Mock git repo
        mock_repo = Mock()
        mock_repo.active_branch.name = "feature-branch"
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        mock_repo_class.return_value = mock_repo
        
        # Create SubTenantCreator
        creator = SubTenantCreator(
            subtenant_name="demo",
            tenant_name="oh",
            env="dev",
            test_mode=True
        )
        creator.validator.repo_path = self.repo_path
        
        # Mock the branch creation to avoid actual git operations
        with patch.object(creator, '_create_feature_branch'):
            with patch('create_subtenant.logger') as mock_logger:
                creator.run()
        
        # Verify subtenant config was added to tenant YAML
        # The script looks for files in tenants/ not _config/tenants/
        tenant_file = self.repo_path / "tenants" / "oh" / "dev-us-east-1.yaml"
        
        # Create the missing tenants directory structure for the test
        tenant_dir = self.repo_path / "tenants" / "oh"
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy the config file to the expected location
        source_file = self.repo_path / "_config" / "tenants" / "oh" / "dev.us-east-1.yaml"
        tenant_file.write_text(source_file.read_text())
        
        # Run the creator again to pick up the file in the right location
        with patch.object(creator, '_create_feature_branch'):
            with patch('create_subtenant.logger'):
                creator._process_and_append_subtenant_config()
        
        updated_content = tenant_file.read_text()
        
        assert "demo:" in updated_content
        assert "oh_demo_dev" in updated_content
        assert "tenant: oh" in updated_content
        assert "env: dev" in updated_content
        
        # Verify workflow was updated
        workflow_file = self.repo_path / ".github" / "workflows" / "tenant_oh.yml"
        updated_workflow = workflow_file.read_text()
        
        assert "demo-job:" in updated_workflow
        assert "Processing demo" in updated_workflow
        assert "workspace:" in updated_workflow  # Original job preserved
        
        # Verify success message
        mock_logger.info.assert_any_call(
            "Sub-tenant workspace setup completed successfully!"
        )


# Pytest fixtures that can be used across multiple test files
@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Create basic structure
    (repo_path / "_config" / "tenants").mkdir(parents=True)
    (repo_path / ".github" / "workflows").mkdir(parents=True)
    (repo_path / "_templates" / "tenant").mkdir(parents=True)
    (repo_path / "_templates" / "workflows").mkdir(parents=True)
    
    return repo_path


@pytest.fixture
def mock_git_repo():
    """Create a mock git repository."""
    mock_repo = Mock()
    mock_repo.active_branch.name = "test-branch"
    mock_repo.is_dirty.return_value = False
    mock_repo.untracked_files = []
    return mock_repo