"""Unit tests for WorkflowConfig loading.

Tests the workflow configuration loading from YAML files.
"""

from pathlib import Path

import pytest

from src.bot.conversations.workflow_config import (
    InputType,
    StateConfig,
    TransitionConfig,
    WorkflowConfig,
    load_all_workflows,
    load_workflow,
)


class TestWorkflowConfig:
    """Test suite for WorkflowConfig Pydantic models.

    Tests the Pydantic models and YAML loading functions.
    """

    def test_transition_config_defaults(self) -> None:
        """Test TransitionConfig with default values.

        This test verifies that TransitionConfig can be created
        with minimal required fields.
        """
        transition = TransitionConfig(target="idle")
        assert transition.target == "idle"
        assert transition.guard is None
        assert transition.action is None

    def test_transition_config_with_all_fields(self) -> None:
        """Test TransitionConfig with all fields.

        This test verifies that all optional fields are set correctly.
        """
        transition = TransitionConfig(
            target="completed",
            guard="is_valid_user",
            action="create_user",
        )
        assert transition.target == "completed"
        assert transition.guard == "is_valid_user"
        assert transition.action == "create_user"

    def test_state_config_defaults(self) -> None:
        """Test StateConfig with default values.

        This test verifies that StateConfig uses correct defaults.
        """
        state = StateConfig()
        assert state.input_type == InputType.NONE
        assert state.validation is None
        assert state.on_valid is None
        assert state.on_invalid is None
        assert state.timeout_seconds is None

    def test_state_config_with_text_input(self) -> None:
        """Test StateConfig with text input type.

        This test verifies a complete text input state configuration.
        """
        state = StateConfig(
            input_type=InputType.TEXT,
            validation="validate_birth_date",
            on_valid=TransitionConfig(target="completed", action="save_data"),
            on_invalid=TransitionConfig(target="same_state", action="show_error"),
            timeout_seconds=300,
        )
        assert state.input_type == InputType.TEXT
        assert state.validation == "validate_birth_date"
        assert state.on_valid.target == "completed"
        assert state.on_invalid.target == "same_state"
        assert state.timeout_seconds == 300

    def test_workflow_config_creation(self) -> None:
        """Test WorkflowConfig creation.

        This test verifies complete workflow configuration.
        """
        workflow = WorkflowConfig(
            name="registration",
            initial_state="start_birth_date",
            states={
                "start_birth_date": StateConfig(
                    input_type=InputType.TEXT,
                    validation="validate_birth_date",
                ),
                "completed": StateConfig(input_type=InputType.NONE),
            },
        )
        assert workflow.name == "registration"
        assert workflow.initial_state == "start_birth_date"
        assert len(workflow.states) == 2
        assert "start_birth_date" in workflow.states
        assert "completed" in workflow.states

    def test_input_type_enum_values(self) -> None:
        """Test InputType enum has correct values.

        This test verifies that InputType enum values match
        expected string representations.
        """
        assert InputType.TEXT.value == "text"
        assert InputType.CALLBACK.value == "callback"
        assert InputType.NONE.value == "none"


class TestLoadWorkflow:
    """Test suite for load_workflow function.

    Tests loading workflow configurations from YAML files.
    """

    def test_load_registration_workflow(self) -> None:
        """Test loading registration.yaml workflow.

        This test verifies that the registration workflow file
        is correctly parsed.
        """
        workflow_path = Path(
            "/mnt/c/Users/AnatolKhmialeuski/Workspace/"
            "telegram_myweeks_life_bot/config/workflows/registration.yaml"
        )
        if not workflow_path.exists():
            pytest.skip("Registration workflow file not found")

        workflow = load_workflow(file_path=workflow_path)
        assert workflow.name == "registration"
        assert workflow.initial_state == "start_birth_date"
        assert "start_birth_date" in workflow.states

    def test_load_settings_workflow(self) -> None:
        """Test loading settings.yaml workflow.

        This test verifies that the settings workflow file
        is correctly parsed.
        """
        workflow_path = Path(
            "/mnt/c/Users/AnatolKhmialeuski/Workspace/"
            "telegram_myweeks_life_bot/config/workflows/settings.yaml"
        )
        if not workflow_path.exists():
            pytest.skip("Settings workflow file not found")

        workflow = load_workflow(file_path=workflow_path)
        assert workflow.name == "settings"
        assert "settings_birth_date" in workflow.states
        assert "settings_life_expectancy" in workflow.states


class TestLoadAllWorkflows:
    """Test suite for load_all_workflows function.

    Tests loading all workflow files from a directory.
    """

    def test_load_all_from_workflows_directory(self) -> None:
        """Test loading all workflows from config/workflows.

        This test verifies that all workflow files in the
        workflows directory are loaded.
        """
        workflows_dir = Path(
            "/mnt/c/Users/AnatolKhmialeuski/Workspace/"
            "telegram_myweeks_life_bot/config/workflows"
        )
        if not workflows_dir.exists():
            pytest.skip("Workflows directory not found")

        workflows = load_all_workflows(workflows_dir=workflows_dir)
        assert len(workflows) >= 2
        assert "registration" in workflows
        assert "settings" in workflows

    def test_load_all_from_empty_directory(self, tmp_path: Path) -> None:
        """Test loading from empty directory returns empty dict.

        This test verifies that an empty directory results in
        an empty workflows dictionary.
        """
        workflows = load_all_workflows(workflows_dir=tmp_path)
        assert workflows == {}

    def test_load_all_from_nonexistent_directory(self) -> None:
        """Test loading from non-existent directory returns empty dict.

        This test verifies that a non-existent directory results in
        an empty workflows dictionary without raising an error.
        """
        workflows = load_all_workflows(workflows_dir=Path("/nonexistent/directory"))
        assert workflows == {}
