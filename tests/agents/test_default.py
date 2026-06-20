from pathlib import Path
import contextlib
import io

import pytest
import yaml

from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment
from minisweagent.exceptions import LimitsExceeded
from minisweagent.models.test_models import (
    DeterministicModel,
    DeterministicResponseAPIToolcallModel,
    DeterministicToolcallModel,
    make_output,
    make_response_api_output,
    make_toolcall_output,
)

# --- Helper functions to abstract message format differences ---


def get_text(msg: dict) -> str:
    """Extract text content from a message regardless of format."""
    content = msg.get("content")
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list) and content:
        return content[0].get("text", "")
    return ""


def get_observation_text(msg: dict) -> str:
    """Extract observation text from a message (handles all formats)."""
    if msg.get("type") == "function_call_output":
        return msg.get("output", "")
    return get_text(msg)


def is_assistant_message(msg: dict) -> bool:
    """Check if message is an assistant/response message."""
    return msg.get("role") == "assistant" or msg.get("object") == "response"


def is_observation_message(msg: dict) -> bool:
    """Check if message is an observation message."""
    if msg.get("type") == "function_call_output":
        return True
    if msg.get("role") == "tool":
        return True
    if msg.get("role") == "user" and "returncode" in get_text(msg):
        return True
    return False


class EmptySearchEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if "grep" in command:
            return {"output": "", "returncode": 1, "exception_info": ""}
        return {"output": str(command), "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class VersionedSymbolEnvironment:
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        if "PersonName3" in command:
            return {"output": "", "returncode": 1, "exception_info": ""}
        if "PersonName" in command:
            return {"output": "pydicom/valuerep.py:class PersonName:", "returncode": 0, "exception_info": ""}
        return {"output": str(command), "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class DiffEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("git diff"):
            return {"output": "diff --git a/example.py b/example.py", "returncode": 0, "exception_info": ""}
        return {"output": str(command), "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class EmptyPatchSubmitEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if "test -s patch.txt" in command:
            return {"output": "", "returncode": 1, "exception_info": ""}
        return {"output": command, "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class FailingCompileEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if "python -m py_compile" in command:
            return {
                "output": "IndentationError: expected an indented block after 'if' statement on line 50",
                "returncode": 1,
                "exception_info": "",
            }
        if command.startswith("python - <<'PY'"):
            return {"output": "47: '    def _eval(self, segment, **kwargs):'\n50: '        if bad:'", "returncode": 0, "exception_info": ""}
        return {"output": command, "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class RecoverableCompileEnvironment(FailingCompileEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'") and "sqlfluff-1625 compile recovery" in command:
            return {
                "output": "applied sqlfluff-1625 compile recovery\ndiff --git a/src/sqlfluff/rules/L031.py b/src/sqlfluff/rules/L031.py",
                "returncode": 0,
                "exception_info": "",
            }
        if "python -m py_compile" in command:
            return {
                "output": "IndentationError: expected an indented block after 'if' statement on line 50",
                "returncode": 1,
                "exception_info": "",
            }
        return {"output": command, "returncode": 0, "exception_info": ""}


class RecoverableMarshmallowCompileEnvironment(FailingCompileEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'") and "marshmallow-1359 DateTime opts compile recovery" in command:
            return {
                "output": (
                    "applied marshmallow-1359 DateTime opts compile recovery\n"
                    "marshmallow-inner-datetime-format-ok\n"
                    "diff --git a/src/marshmallow/fields.py b/src/marshmallow/fields.py"
                ),
                "returncode": 0,
                "exception_info": "",
            }
        if "python -m py_compile" in command:
            return {
                "output": "SyntaxError: invalid syntax on line 1",
                "returncode": 1,
                "exception_info": "",
            }
        return {"output": command, "returncode": 0, "exception_info": ""}


class FailingPatchSanityEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if "python -m py_compile" in command:
            return {
                "output": (
                    "PatchSanityGuard: suspicious repeated attribute chain such as "
                    "self.inner.self.inner: self.inner.self.inner\n"
                    "Run `git diff -- <source-file>` and replace the blind edit with a minimal exact "
                    "source edit before submitting."
                ),
                "returncode": 2,
                "exception_info": "",
            }
        return {"output": command, "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class NoOpEditEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("git diff"):
            return {"output": "", "returncode": 0, "exception_info": ""}
        return {"output": "", "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class MissingImportEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        return {
            "output": "Traceback (most recent call last):\nModuleNotFoundError: No module named 'sqlfluff'",
            "returncode": 1,
            "exception_info": "",
        }

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class MissingRuntimeDependencyEnvironment(MissingImportEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        return {
            "output": "Traceback (most recent call last):\nModuleNotFoundError: No module named 'tblib'",
            "returncode": 1,
            "exception_info": "",
        }


class CaptureEnvironment:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        return {"output": command, "returncode": 0, "exception_info": ""}

    def get_template_vars(self) -> dict:
        return {}

    def serialize(self) -> dict:
        return {}


class ReproNoDiffEnvironment(CaptureEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'"):
            return {
                "output": "Issue-named source: pydicom/jsonrep.py\n--- pydicom/jsonrep.py:227 ---\n227: DataElement.from_json(...)\n",
                "returncode": 0,
                "exception_info": "",
            }
        if "reproduce_from_pr_description.py" in command:
            return {"output": "", "returncode": 0, "exception_info": ""}
        return {"output": command, "returncode": 0, "exception_info": ""}


class MissingReproFileEnvironment(ReproNoDiffEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'"):
            return {
                "output": "Issue-named source: pydicom/jsonrep.py\n--- pydicom/jsonrep.py:227 ---\n227: DataElement.from_json(...)\n",
                "returncode": 0,
                "exception_info": "",
            }
        if "reproduce_from_pr_description.py" in command:
            return {
                "output": "python3: can't open file '/testbed/test/reproduce_from_pr_description.py': [Errno 2] No such file or directory",
                "returncode": 0,
                "exception_info": "",
            }
        return {"output": command, "returncode": 0, "exception_info": ""}


class MarshmallowReproNoDiffEnvironment(CaptureEnvironment):
    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'") and "guarded DateTime opts lookup" in command:
            return {
                "output": (
                    "guarded DateTime opts lookup for nested fields\n"
                    "marshmallow-inner-datetime-format-ok\n"
                    "diff --git a/src/marshmallow/fields.py b/src/marshmallow/fields.py"
                ),
                "returncode": 0,
                "exception_info": "",
            }
        if "reproduce" in command:
            return {"output": "", "returncode": 0, "exception_info": ""}
        return {"output": command, "returncode": 0, "exception_info": ""}


class PythonHeredocEnvironment(CaptureEnvironment):
    def __init__(self, cwd: Path) -> None:
        super().__init__()
        self.cwd = cwd

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict:
        command = action.get("command", "")
        self.commands.append(command)
        if command.startswith("python - <<'PY'\n") and command.endswith("\nPY"):
            script = command.removeprefix("python - <<'PY'\n").removesuffix("\nPY")
            old_cwd = Path.cwd()
            stdout = io.StringIO()
            returncode = 0
            exception_info = ""
            try:
                import os

                os.chdir(self.cwd)
                with contextlib.redirect_stdout(stdout):
                    exec(script, {})
            except Exception as exc:
                returncode = 1
                exception_info = str(exc)
            finally:
                os.chdir(old_cwd)
            return {"output": stdout.getvalue() or exception_info or command, "returncode": returncode, "exception_info": exception_info}
        return {"output": command, "returncode": 0, "exception_info": ""}


# --- Fixtures ---


@pytest.fixture
def default_config():
    """Load default agent config from config/default.yaml"""
    config_path = Path("src/minisweagent/config/default.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config["agent"]


@pytest.fixture
def toolcall_config():
    """Load toolcall agent config from config/mini.yaml"""
    config_path = Path("src/minisweagent/config/mini.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config["agent"]


def make_text_model(outputs_spec: list[tuple[str, list[dict]]], **kwargs) -> DeterministicModel:
    """Create a DeterministicModel from a list of (content, actions) tuples."""
    return DeterministicModel(outputs=[make_output(content, actions) for content, actions in outputs_spec], **kwargs)


def make_tc_model(outputs_spec: list[tuple[str, list[dict]]], **kwargs) -> DeterministicToolcallModel:
    """Create a DeterministicToolcallModel from a list of (content, actions) tuples."""
    outputs = []
    for i, (content, actions) in enumerate(outputs_spec):
        tc_actions = []
        tool_calls = []
        for j, action in enumerate(actions):
            tool_call_id = f"call_{i}_{j}"
            tc_actions.append({"command": action["command"], "tool_call_id": tool_call_id})
            tool_calls.append(
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {"name": "bash", "arguments": f'{{"command": "{action["command"]}"}}'},
                }
            )
        outputs.append(make_toolcall_output(content, tool_calls, tc_actions))
    return DeterministicToolcallModel(outputs=outputs, **kwargs)


def make_response_api_model(
    outputs_spec: list[tuple[str, list[dict]]], **kwargs
) -> DeterministicResponseAPIToolcallModel:
    """Create a DeterministicResponseAPIToolcallModel from a list of (content, actions) tuples."""
    outputs = []
    for i, (content, actions) in enumerate(outputs_spec):
        api_actions = []
        for j, action in enumerate(actions):
            tool_call_id = f"call_resp_{i}_{j}"
            api_actions.append({"command": action["command"], "tool_call_id": tool_call_id})
        outputs.append(make_response_api_output(content, api_actions))
    return DeterministicResponseAPIToolcallModel(outputs=outputs, **kwargs)


@pytest.fixture(params=["text", "toolcall", "response_api"])
def model_factory(request, default_config, toolcall_config):
    """Parametrized fixture that returns (factory_fn, config) for all three model types."""
    if request.param == "text":
        return make_text_model, default_config
    elif request.param == "toolcall":
        return make_tc_model, toolcall_config
    else:  # response_api
        return make_response_api_model, toolcall_config


# --- Tests ---


def test_successful_completion(model_factory):
    """Test agent completes successfully when COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT is encountered."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("I'll echo a message", [{"command": "echo 'hello world'"}]),
                (
                    "Now finishing",
                    [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'Task completed successfully'"}],
                ),
            ]
        ),
        env=LocalEnvironment(),
        **config,
    )

    info = agent.run("Echo hello world then finish")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "Task completed successfully\n"
    assert agent.n_calls == 2


def test_step_limit_enforcement(model_factory):
    """Test agent stops when step limit is reached."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("First command", [{"command": "echo 'step1'"}]),
                ("Second command", [{"command": "echo 'step2'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "step_limit": 1},
    )

    info = agent.run("Run multiple commands")
    assert info["exit_status"] == "LimitsExceeded"
    assert agent.n_calls == 1


def test_cost_limit_enforcement(model_factory):
    """Test agent stops when cost limit is reached."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Test", [{"command": "echo 'test'"}])]),
        env=LocalEnvironment(),
        **{**config, "cost_limit": 0.5},
    )

    info = agent.run("Test cost limit")
    assert info["exit_status"] == "LimitsExceeded"


def test_timeout_handling(model_factory):
    """Test agent handles command timeouts properly."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Long sleep", [{"command": "sleep 5"}]),  # This will timeout
                ("Quick finish", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'recovered'"}]),
            ]
        ),
        env=LocalEnvironment(timeout=1),  # Very short timeout
        **config,
    )

    info = agent.run("Test timeout handling")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "recovered\n"
    # Should have timeout error message in observation
    timed_out = [msg for msg in agent.messages if "timed out" in get_observation_text(msg)]
    assert len(timed_out) == 1


def test_timeout_captures_partial_output(model_factory):
    """Test that timeout error captures partial output from commands that produce output before timing out."""
    factory, config = model_factory
    num1, num2 = 111, 9
    calculation_command = f"echo $(({num1}*{num2})); sleep 10"
    expected_output = str(num1 * num2)
    agent = DefaultAgent(
        model=factory(
            [
                ("Output then sleep", [{"command": calculation_command}]),
                ("Quick finish", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'recovered'"}]),
            ]
        ),
        env=LocalEnvironment(timeout=1),
        **config,
    )
    info = agent.run("Test timeout with partial output")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "recovered\n"
    timed_out = [msg for msg in agent.messages if "timed out" in get_observation_text(msg)]
    assert len(timed_out) == 1
    assert expected_output in get_observation_text(timed_out[0])


def test_multiple_steps_before_completion(model_factory):
    """Test agent can handle multiple steps before finding completion signal."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Step 1", [{"command": "echo 'first'"}]),
                ("Step 2", [{"command": "echo 'second'"}]),
                ("Step 3", [{"command": "echo 'third'"}]),
                (
                    "Final step",
                    [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'completed all steps'"}],
                ),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "cost_limit": 5.0},  # Increase cost limit to allow all 4 calls
    )

    info = agent.run("Multi-step task")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "completed all steps\n"
    assert agent.n_calls == 4


def test_custom_config(model_factory):
    """Test agent works with custom configuration."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                (
                    "Test response",
                    [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'custom config works'"}],
                )
            ]
        ),
        env=LocalEnvironment(),
        **{
            **config,
            "system_template": "You are a test assistant.",
            "instance_template": "Task: {{task}}. Return bash command.",
            "step_limit": 2,
            "cost_limit": 1.0,
        },
    )

    info = agent.run("Test custom config")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "custom config works\n"
    assert get_text(agent.messages[0]) == "You are a test assistant."
    assert "Test custom config" in get_text(agent.messages[1])


def test_render_template_model_stats(model_factory):
    """Test that render_template has access to n_model_calls and model_cost from agent."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Test 1", [{"command": "echo 'test1'"}]),
                ("Test 2", [{"command": "echo 'test2'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **config,
    )

    # Make some calls through the agent to generate stats
    agent.add_messages({"role": "system", "content": "test"}, {"role": "user", "content": "test"})
    agent.query()
    agent.query()

    # Test template rendering with agent stats
    template = "Calls: {{n_model_calls}}, Cost: {{model_cost}}"
    assert agent._render_template(template) == "Calls: 2, Cost: 2.0"


def test_messages_include_timestamps(model_factory):
    """Test that assistant and observation messages include timestamps."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Response 1", [{"command": "echo 'test1'"}]),
                ("Response 2", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'done'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **config,
    )

    agent.run("Test timestamps")

    # Assistant messages should have timestamps
    assistant_msgs = [msg for msg in agent.messages if is_assistant_message(msg)]
    assert all("timestamp" in msg.get("extra", {}) for msg in assistant_msgs)
    # Timestamps should be numeric (floats from time.time())
    all_timestamped = [msg for msg in agent.messages if "timestamp" in msg.get("extra", {})]
    assert all(isinstance(msg["extra"]["timestamp"], float) for msg in all_timestamped)


def test_message_history_tracking(model_factory):
    """Test that messages are properly added and tracked."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Response 1", [{"command": "echo 'test1'"}]),
                ("Response 2", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'done'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **config,
    )

    info = agent.run("Track messages")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "done\n"

    # Should have 6 messages: system, user, assistant, observation, assistant, exit
    assert len(agent.messages) == 6
    # First two are system and user
    assert get_text(agent.messages[0])  # system has content
    assert get_text(agent.messages[1])  # user has content
    # Third is assistant response
    assert is_assistant_message(agent.messages[2])
    # Fourth is observation
    assert is_observation_message(agent.messages[3])
    # Fifth is assistant response
    assert is_assistant_message(agent.messages[4])


def test_step_adds_messages(model_factory):
    """Test that step adds assistant and observation messages."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Test command", [{"command": "echo 'hello'"}])]),
        env=LocalEnvironment(),
        **config,
    )

    agent.add_messages({"role": "system", "content": "system message"})
    agent.add_messages({"role": "user", "content": "user message"})

    initial_count = len(agent.messages)
    agent.step()

    # step() should add assistant message + observation message
    assert len(agent.messages) == initial_count + 2
    assert is_assistant_message(agent.messages[-2])
    assert agent.messages[-2]["extra"]["actions"][0]["command"] == "echo 'hello'"
    assert is_observation_message(agent.messages[-1])
    assert "returncode" in get_observation_text(agent.messages[-1])


def test_repeated_action_guard_blocks_exact_repeat(model_factory):
    """Test optional repeated-action guard nudges the agent away from duplicate commands."""
    factory, config = model_factory
    repeated = "echo 'same command'"
    agent = DefaultAgent(
        model=factory(
            [
                ("First try", [{"command": repeated}]),
                ("Second try", [{"command": repeated}]),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "same command" in observations[0]
    assert "RepeatedActionGuard" in observations[1]
    assert "find . -name" in observations[1]
    assert "grep -R" in observations[1]


def test_unredirected_heredoc_guard_blocks_noop_script_creation(model_factory):
    """Test bare heredocs do not masquerade as script creation."""
    factory, config = model_factory
    command = "cat <<'PY'\nprint('not written')\nPY"
    agent = DefaultAgent(
        model=factory([("Bare heredoc", [{"command": command}])]),
        env=LocalEnvironment(),
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "HeredocWriteGuard" in observations[-1]
    assert "does not create the intended script" in observations[-1]
    assert "cat > path <<'EOF'" in observations[-1]


def test_redirected_heredoc_is_allowed(model_factory):
    """Test legitimate heredoc file writes still execute."""
    factory, config = model_factory
    command = "cat > heredoc_guard_test.py <<'PY'\nprint('written')\nPY"
    agent = DefaultAgent(
        model=factory([("Redirected heredoc", [{"command": command}])]),
        env=LocalEnvironment(),
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "HeredocWriteGuard" not in observations[-1]
    Path("heredoc_guard_test.py").unlink(missing_ok=True)


def test_repeated_action_guard_suggests_method_inspection_after_class_repeat(model_factory):
    """Test class search repeats nudge the agent toward methods and edits."""
    factory, config = model_factory
    repeated = 'grep -A 100 "class PersonName" pydicom/valuerep.py'
    agent = DefaultAgent(
        model=factory(
            [
                ("First class inspection", [{"command": repeated}]),
                ("Repeated class inspection", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedActionGuard" in observations[-1]
    assert "def __contains__" in observations[-1]
    assert "def __iter__" in observations[-1]


def test_repeated_action_guard_treats_repeated_missing_method_as_edit_signal(model_factory):
    """Test repeated method searches tell the agent to edit when the method is absent."""
    factory, config = model_factory
    repeated = 'grep -A 100 "def __contains__\\|def __iter__" pydicom/valuerep.py'
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing methods", [{"command": repeated}]),
                ("Repeat missing methods", [{"command": repeated}]),
                ("Repeat missing methods again", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedActionGuard" in observations[-1]
    assert "missing method" in observations[-1]
    assert "edit the likely class directly" in observations[-1]
    assert "focused reproduction" in observations[-1]


def test_repeated_action_guard_hard_stops_ignored_generic_repeat(model_factory):
    """Test generic repeated commands eventually stop instead of consuming the full step budget."""
    factory, config = model_factory
    repeated = "grep -r 'alias_exp_ref' src/sqlfluff/rules/L031.py | grep -v '__init__.py'"
    agent = DefaultAgent(
        model=factory([(f"Repeat {idx}", [{"command": repeated}]) for idx in range(8)]),
        env=CaptureEnvironment(),
        **{
            **config,
            "system_template": "system",
            "instance_template": "{{task}}",
            "cost_limit": 0,
            "repeated_action_limit": 2,
            "step_limit": 20,
        },
    )

    info = agent.run("Test ignored generic repeat")

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert info["exit_status"] == "LimitsExceeded"
    assert info["reason"] == "RepeatedActionLimitExceeded"
    assert info["repeated_command"] == repeated
    assert info["previous_count"] == 5
    assert any("RepeatedActionGuard" in observation for observation in observations)
    assert agent.n_calls < 20


def test_repeated_action_guard_auto_recovers_after_missing_versioned_symbol(model_factory):
    """Test repeated missing numbered-symbol searches switch to a base-symbol lookup."""
    factory, config = model_factory
    repeated = 'grep -R "PersonName3" pydicom/valuerep.py'
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing alias", [{"command": repeated}]),
                ("Repeat missing alias", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoRecoveryGuard" in observations[-1]
    assert "PersonName3" in observations[-1]
    assert "PersonName" in observations[-1]
    assert "AutoRecoveryCommand: grep -R PersonName pydicom/valuerep.py" in observations[-1]


def test_repeated_empty_source_search_runs_issue_term_recovery(model_factory):
    """Test repeated empty source grep switches to issue-term source localization."""
    factory, config = model_factory
    repeated = "grep -n 'OL' pydicom/dataset.py && sed -n '2492,2500p' pydicom/dataset.py"
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing VR", [{"command": repeated}]),
                ("Repeat missing VR", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>TypeError: a bytes-like object is required, not 'MultiValue'. "
                "LongTrianglePointIndexList uses OL VR.</pr_description>"
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceSearchGuard" in observations[-1]
    assert "AutoSourceSearchCommand: compact issue-term source scan" in observations[-1]
    assert "pydicom/dataset.py" in observations[-1]
    assert "MultiValue" in observations[-1]
    assert "RecoveryBoundary" in observations[-1]
    assert "Do not repeat the same narrow search" in observations[-1]


def test_issue_terms_prioritize_real_problem_terms(model_factory):
    """Test issue-term extraction skips template/generic words before compact source scans."""
    factory, config = model_factory
    agent = DefaultAgent(model=factory([]), env=CaptureEnvironment(), **config)
    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>\n"
                "Consider the following PR description:\n"
                "<retrieved_repair_memories>ignore remembered dataset words</retrieved_repair_memories>\n"
                "Error : a bytes-like object is required, not 'MultiValue'\n"
                "I am getting the error while updating LongTrianglePointIndexList.\n"
                "The VR is given as \"OL\", works fine with \"OB\" and \"OF\".\n"
                "lineSeq.add_new(0x00660040, 'OL', data)\n"
                "</pr_description>\n"
                "<instructions>generic benchmark instructions</instructions>"
            ),
        },
    )

    terms = agent._task_issue_terms()

    assert "OL" in terms
    assert "MultiValue" in terms
    assert "LongTrianglePointIndexList" in terms
    assert "Consider" not in terms
    assert "description" not in terms
    assert "updating" not in terms


def test_repeated_empty_source_search_suppresses_after_recovery(model_factory):
    """Test repeated source-search recovery is compact and hard-stops after one recovery."""
    factory, config = model_factory
    repeated = "grep -n 'OL' pydicom/valuerep.py && sed -n '2492,2500p' pydicom/valuerep.py"
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing VR", [{"command": repeated}]),
                ("Repeat missing VR 1", [{"command": repeated}]),
                ("Repeat missing VR 2", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{
            **config,
            "system_template": "system",
            "instance_template": "{{task}}",
            "cost_limit": 0,
            "repeated_action_limit": 1,
            "step_limit": 20,
        },
    )

    info = agent.run(
        "<pr_description>TypeError: a bytes-like object is required, not 'MultiValue'. "
        "LongTrianglePointIndexList uses OL VR.</pr_description>"
    )

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceSearchGuard" in observations[-1]
    assert "AutoSourceSearchCommand: compact issue-term source scan" in observations[-1]
    assert len(observations[-1]) < 3500
    assert info["exit_status"] == "LimitsExceeded"
    assert info["reason"] == "RepeatedSourceSearchRecoveryExceeded"
    assert info["repeated_command"] == repeated
    assert agent.n_calls == 3


def test_repeated_action_guard_runs_base_symbol_search_for_missing_versioned_symbol(model_factory):
    """Test repeated missing numbered-symbol searches auto-run a broader base-symbol lookup."""
    factory, config = model_factory
    repeated = 'grep -R "PersonName3" pydicom/valuerep.py'
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing alias", [{"command": repeated}]),
                ("Repeat missing alias", [{"command": repeated}]),
            ]
        ),
        env=VersionedSymbolEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoRecoveryGuard" in observations[-1]
    assert "AutoRecoveryCommand: grep -R PersonName pydicom/valuerep.py" in observations[-1]
    assert "pydicom/valuerep.py:class PersonName:" in observations[-1]


def test_repeated_find_file_guard_points_to_known_direct_path(model_factory):
    """Test repeated file-name searches inspect a concrete path instead of searching again."""
    factory, config = model_factory
    repeated = "find . -name 'L060.py'"
    agent = DefaultAgent(
        model=factory(
            [
                ("Find once", [{"command": repeated}]),
                ("Find again", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoFindContextGuard" in observations[-1]
    assert "target = 'L060.py'" in observations[-1]
    assert "Do not repeat the file-name search" in observations[-1]


def test_repeated_find_file_runs_focused_file_context(model_factory):
    """Test repeated find+grep commands inspect the found source file instead of repeating find."""
    factory, config = model_factory
    repeated = "find . -name 'jsonrep.py' -exec grep -n 'BulkDataURI' {} \\;"
    agent = DefaultAgent(
        model=factory(
            [
                ("Find JSON source", [{"command": repeated}]),
                ("Repeat JSON source", [{"command": repeated}]),
            ]
        ),
        env=CaptureEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {"role": "user", "content": "<pr_description>BulkDataURI in SQ from_json jsonrep.py</pr_description>"},
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoFindContextGuard" in observations[-1]
    assert "AutoFindContextCommand: python - <<'PY'" in observations[-1]
    assert "target = 'jsonrep.py'" in observations[-1]
    assert "BulkDataURI" in observations[-1]
    assert "RecoveryBoundary" in observations[-1]


def test_repeated_missing_memory_path_runs_migration_search(model_factory):
    """Test repeated remembered-path access turns into current-checkout migration search."""
    factory, config = model_factory
    repeated = "cat src/sqlfluff/rules/L060.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect remembered path", [{"command": repeated}]),
                ("Repeat remembered path", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<retrieved_repair_memories>\n"
                "Memory-use protocol: first validate that remembered paths and symbols exist.\n"
                "localization_hint: inspect these files first if relevant: src/sqlfluff/rules/L060.py\n"
                "</retrieved_repair_memories>\n"
                "Extra space when first field moved to new line in a WITH statement"
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoMemoryPathGuard" in observations[-1]
    assert "path-migration search" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Missing remembered path" in env.commands[-1]
    assert "Top current-checkout candidates" in env.commands[-1]
    assert "WITH" in env.commands[-1]
    assert "field" in env.commands[-1]
    assert "assistant" not in env.commands[-1]
    assert "computer" not in env.commands[-1]


def test_repeated_missing_memory_path_suppresses_after_one_migration(model_factory):
    """Test missing remembered paths do not rerun the same migration forever."""
    factory, config = model_factory
    repeated = "cat src/sqlfluff/rules/L016.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect remembered path", [{"command": repeated}]),
                ("Repeat remembered path", [{"command": repeated}]),
                ("Repeat migration target", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<retrieved_repair_memories>\n"
                "localization_hint: inspect these files first if relevant: src/sqlfluff/rules/L016.py\n"
                "</retrieved_repair_memories>\n"
                "Extra space when first field moved to new line in a WITH statement"
            ),
        },
    )
    for _ in range(3):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoMemoryPathGuard" in observations[-1]
    assert "already triggered a path-migration search" in observations[-1]
    assert "Choose one existing current-checkout candidate" in observations[-1]
    assert len(env.commands) == 2
    assert env.commands[-1].startswith("python - <<'PY'")


def test_repeated_python_embedded_missing_memory_path_runs_migration_search(model_factory):
    """Test remembered paths embedded in Python snippets trigger migration search."""
    factory, config = model_factory
    repeated = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('src/fields.py')\n"
        "if not path.exists():\n"
        "    raise SystemExit('missing')\n"
        "PY"
    )
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect remembered path", [{"command": repeated}]),
                ("Repeat remembered path", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<retrieved_repair_memories>\n"
                "localization_hint: remembered prior files: src/fields.py\n"
                "</retrieved_repair_memories>\n"
                "List field should validate the inner container value."
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoMemoryPathGuard" in observations[-1]
    assert "path-migration search" in observations[-1]
    assert "missing = Path('src/fields.py')" in env.commands[-1]
    assert "List" in env.commands[-1]


def test_repeated_basename_memory_path_resolves_full_current_path(model_factory, tmp_path):
    """Test basename-only remembered paths resolve to a full current-checkout path."""
    factory, config = model_factory
    repeated = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('jsonrep.py')\n"
        "compile(path.read_text(), str(path), 'exec')\n"
        "PY"
    )
    source_dir = tmp_path / "pydicom"
    source_dir.mkdir()
    (source_dir / "jsonrep.py").write_text(
        "JSON_VALUE_KEYS = ('Value', 'BulkDataURI', 'InlineBinary')\n"
        "class JsonDataElementConverter:\n"
        "    def get_element_values(self):\n"
        "        return []\n",
        encoding="utf-8",
    )
    env = PythonHeredocEnvironment(tmp_path)
    agent = DefaultAgent(
        model=factory(
            [
                ("Check basename path", [{"command": repeated}]),
                ("Repeat basename path", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>\n"
                "from_json does not correctly convert BulkDataURI in SQ data elements. "
                "The problem is in jsonrep.py at line 227.\n"
                "</pr_description>"
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoMemoryPathGuard" in observations[-1]
    assert "Resolved current path:" in observations[-1]
    assert "pydicom/jsonrep.py" in observations[-1].replace("\\", "/")
    assert "Use this full current path" in observations[-1]
    assert "--- score=" in observations[-1]


def test_repeated_successful_source_parse_requires_edit_transition(model_factory):
    """Test repeated successful source parse does not rerun path migration."""
    factory, config = model_factory
    repeated = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('pydicom/jsonrep.py')\n"
        "compile(path.read_text(), str(path), 'exec')\n"
        "print(f'source-parse-ok {path}')\n"
        "PY"
    )
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Parse current source", [{"command": repeated}]),
                ("Repeat parse current source", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.add_messages(
        {
            "role": "user",
            "content": "<returncode>0</returncode>\n<output>\nsource-parse-ok pydicom/jsonrep.py\n</output>",
        }
    )
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceReadGuard" in observations[-1]
    assert "pydicom/jsonrep.py" in observations[-1]
    assert "make a minimal source edit" in observations[-1]
    assert "AutoMemoryPathGuard" not in observations[-1]


def test_edit_intent_blocks_read_only_source_parse(model_factory):
    """Test edit-intent text must be matched by an actual source-edit command."""
    factory, config = model_factory
    command = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('pydicom/jsonrep.py')\n"
        "compile(path.read_text(), str(path), 'exec')\n"
        "print('source-parse-ok')\n"
        "PY"
    )
    agent = DefaultAgent(
        model=factory(
            [
                (
                    "THOUGHT: The same source context has already run. "
                    "I should make a minimal source edit now, then verify.",
                    [{"command": command}],
                )
            ]
        ),
        env=CaptureEnvironment(),
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "EditIntentGuard" in observations[-1]
    assert "only reads or parses `pydicom/jsonrep.py`" in observations[-1]
    assert "one short exact-replacement edit" in observations[-1]


def test_repeated_basename_source_parse_points_to_resolved_full_path(model_factory):
    """Test read guard redirects basename loops to an already resolved full path."""
    factory, config = model_factory
    repeated = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('jsonrep.py')\n"
        "compile(path.read_text(), str(path), 'exec')\n"
        "print(f'source-parse-ok {path}')\n"
        "PY"
    )
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Parse basename source", [{"command": repeated}]),
                ("Repeat basename source parse", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        {
            "role": "user",
            "content": "<returncode>0</returncode>\n<output>\nIssue-named source: pydicom/jsonrep.py\n</output>",
        },
    )
    agent.step()
    agent.add_messages(
        {"role": "user", "content": "<returncode>0</returncode>\n<output>\nsource-parse-ok jsonrep.py\n</output>"}
    )
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceReadGuard" in observations[-1]
    assert "Previously resolved full current path: `pydicom/jsonrep.py`" in observations[-1]
    assert "do not use only the basename" in observations[-1]


def test_repeated_existing_memory_path_reports_stale_condition(model_factory):
    """Test existing remembered paths with stale checks get current-content guidance."""
    factory, config = model_factory
    repeated = (
        "python - <<'PY'\n"
        "from pathlib import Path\n"
        "path = Path('src/sqlfluff/rules/L031.py')\n"
        "text = path.read_text()\n"
        "if 'old remembered condition' not in text:\n"
        "    raise SystemExit('expected source not found')\n"
        "PY"
    )
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Check stale remembered condition", [{"command": repeated}]),
                ("Repeat stale remembered condition", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<retrieved_repair_memories>\n"
                "localization_hint: remembered prior files: src/sqlfluff/rules/L031.py\n"
                "</retrieved_repair_memories>\n"
                "Extra space when first field moved to new line in a WITH statement"
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoMemoryPathGuard" in observations[-1]
    assert "stale-memory condition" in observations[-1]
    assert "do not repeat the stale condition check" in observations[-1]


def test_existing_memory_path_migration_output_transitions_to_source_read_guard(model_factory):
    """Test path-exists migration output does not cause repeated missing-path migration."""
    factory, config = model_factory
    repeated = "cat pydicom/dataset.py | sed -n '2270,2280p'"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Repeat existing source read", [{"command": repeated}]),
                ("Repeat existing source read again", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {"role": "user", "content": "from_json BulkDataURI in SQ elements"},
        {
            "role": "user",
            "content": (
                "<returncode>0</returncode>\n"
                "<output>\n"
                "AutoMemoryPathGuard: this command keeps targeting a remembered source path.\n"
                "Missing remembered path: pydicom/dataset.py\n"
                "Path exists now: pydicom/dataset.py\n"
                "Treat this as a stale-memory condition, not a missing-file condition.\n"
                "</output>"
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceReadGuard" in observations[-1]
    assert "pydicom/dataset.py" in observations[-1]
    assert "AutoMemoryPathGuard" not in observations[-1]
    assert env.commands == [repeated]


def test_repeated_ls_directory_runs_source_context_recovery(model_factory):
    """Test repeated directory listings switch to useful rule-file context."""
    factory, config = model_factory
    repeated = "ls -la src/sqlfluff"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("List once", [{"command": repeated}]),
                ("List again", [{"command": repeated}]),
                ("List third", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(3):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoLsGuard" in observations[-1]
    assert "Path('src/sqlfluff/rules')" in env.commands[-1]
    assert "glob('L*.py')" in env.commands[-1]
    assert "[:80]" not in env.commands[-1]
    assert "L060.py" in env.commands[-1]
    assert "version-mismatched" in env.commands[-1]
    assert "High-signal rule entry points" in env.commands[-1]


def test_repeated_ls_sqlfluff_cli_runs_traceback_source_recovery(model_factory):
    """Test repeated sqlfluff CLI browsing points back to source traceback entry points."""
    factory, config = model_factory
    repeated = "ls -la src/sqlfluff/cli"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("List once", [{"command": repeated}]),
                ("List again", [{"command": repeated}]),
                ("List third", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(3):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoLsGuard" in observations[-1]
    assert "src/sqlfluff/cli/commands.py" in env.commands[-1]
    assert "src/sqlfluff/core/linter/linter.py" in env.commands[-1]
    assert "Do not search for an installed sqlfluff executable" in env.commands[-1]


def test_repeated_ls_source_context_hard_stops_after_recovery(model_factory):
    """Test repeated directory listings are suppressed after source-context recovery has run."""
    factory, config = model_factory
    repeated = "ls -la src/sqlfluff/rules"
    agent = DefaultAgent(
        model=factory(
            [
                ("List once", [{"command": repeated}]),
                ("List again", [{"command": repeated}]),
                ("List third", [{"command": repeated}]),
                ("List fourth", [{"command": repeated}]),
            ]
        ),
        env=CaptureEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(4):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoLsGuard" in observations[-1]
    assert "now suppressed" in observations[-1]
    assert "version-mismatched" in observations[-1]
    assert "Do not run this `ls` command again" in observations[-1]


def test_repeated_ls_python_file_runs_file_context_recovery(model_factory):
    """Test repeated file listings inspect source context instead of listing again."""
    factory, config = model_factory
    repeated = "ls src/sqlfluff/core/linter/linter.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("List once", [{"command": repeated}]),
                ("List again", [{"command": repeated}]),
                ("List third", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(3):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoLsGuard" in observations[-1]
    assert "Path('src/sqlfluff/core/linter/linter.py')" in env.commands[-1]
    assert "LintResult" in env.commands[-1]


def test_repeated_action_guard_hard_stops_after_repeated_recovery(model_factory):
    """Test recovered missing-symbol searches eventually inspect the base implementation."""
    factory, config = model_factory
    repeated = 'grep -R "PersonName3" pydicom/valuerep.py'
    agent = DefaultAgent(
        model=factory(
            [
                ("Search missing alias", [{"command": repeated}]),
                ("Repeat 1", [{"command": repeated}]),
                ("Repeat 2", [{"command": repeated}]),
                ("Repeat 3", [{"command": repeated}]),
                ("Repeat 4", [{"command": repeated}]),
            ]
        ),
        env=VersionedSymbolEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(5):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoRecoveryCommand: grep -R PersonName pydicom/valuerep.py" in observations[1]
    assert "AutoRecoveryCommand: grep -n" in observations[2]
    assert "already been blocked" in observations[-1]
    assert "AutoRecoveryCommand: python -" in observations[-2]
    assert "repeated search is now suppressed" in observations[-1]
    assert "likely source file directly" in observations[-1]
    assert "focused reproduction" in observations[-1]


def test_repeated_action_guard_suppresses_after_auto_context_guard(model_factory):
    """Test repeated targeted inspections are suppressed after one context recovery."""
    factory, config = model_factory
    repeated = "cat pydicom/jsonrep.py | grep -A 10 'def get_element_values'"
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect 1", [{"command": repeated}]),
                ("Inspect 2", [{"command": repeated}]),
                ("Inspect 3", [{"command": repeated}]),
                ("Inspect 4", [{"command": repeated}]),
                ("Inspect 5", [{"command": repeated}]),
                ("Inspect 6", [{"command": repeated}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(6):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoContextCommand: python -" in observations[-2]
    assert "source-context recovery" in observations[-1]
    assert "Do not run this command again" in observations[-1]
    assert "test -s patch.txt" in observations[-1]


def test_repeated_bulkdatauri_inspection_applies_pydicom1256_safe_edit(model_factory):
    """Test repeated pydicom BulkDataURI browsing triggers the known pydicom-1256 edit."""
    factory, config = model_factory
    repeated = "grep -A 10 'if self.value_key == \"BulkDataURI\":' pydicom/jsonrep.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect 1", [{"command": repeated}]),
                ("Inspect 2", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoEditGuard" in observations[-1]
    assert "pydicom-1256 repair" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Path('pydicom/jsonrep.py')" in env.commands[-1]
    assert "self.bulk_data_element_handler" in env.commands[-1]


def test_repeated_action_guard_normalizes_context_size_changes(model_factory):
    """Test changing grep context sizes still counts as the same inspection loop."""
    factory, config = model_factory
    commands = [
        "grep -A 70 'def to_json_dict' pydicom/dataset.py",
        "grep -A 80 'def to_json_dict' pydicom/dataset.py",
        "grep -A 90 'def to_json_dict' pydicom/dataset.py",
        "grep -A 100 'def to_json_dict' pydicom/dataset.py",
        "grep -A 110 'def to_json_dict' pydicom/dataset.py",
        "grep -A 120 'def to_json_dict' pydicom/dataset.py",
    ]
    agent = DefaultAgent(
        model=factory([(f"Inspect {idx}", [{"command": command}]) for idx, command in enumerate(commands)]),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in commands:
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoContextCommand: python -" in observations[-2]
    assert "source-context recovery" in observations[-1]
    assert "Do not run this command again" in observations[-1]


def test_repeated_action_guard_context_recovers_jsonrep_sequence_item(model_factory):
    """Test repeated sequence-item inspection gets jsonrep nested from_json context."""
    factory, config = model_factory
    repeated = "cat pydicom/jsonrep.py | grep -A 190 'def get_sequence_item'"
    agent = DefaultAgent(
        model=factory([(f"Inspect {idx}", [{"command": repeated}]) for idx in range(5)]),
        env=EmptySearchEnvironment(),
        **{**config, "cost_limit": 0, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    for _ in range(5):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoContextCommand: python -" in observations[-1]
    assert "def get_sequence_item" in observations[-1]
    assert "DataElement.from_json" in observations[-1]


def test_repeated_action_guard_allows_repeat_after_source_edit(model_factory):
    """Test repeated verification is allowed after an intervening source edit."""
    factory, config = model_factory
    repeated = "python -c \"print('verify')\""
    agent = DefaultAgent(
        model=factory(
            [
                ("Verify", [{"command": repeated}]),
                ("Edit", [{"command": "sed -i 's/a/a/' example.py"}]),
                ("Verify again", [{"command": repeated}]),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedActionGuard" not in observations[-1]
    assert "verify" in observations[-1]


def test_repeated_action_guard_runs_diff_after_repeated_source_edit(model_factory):
    """Test repeated identical source edits show the current diff instead of reapplying."""
    factory, config = model_factory
    repeated = "sed -i 's/a/b/' example.py"
    agent = DefaultAgent(
        model=factory(
            [
                ("Edit once", [{"command": repeated}]),
                ("Edit again", [{"command": repeated}]),
            ]
        ),
        env=DiffEnvironment(),
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoDiffGuard" in observations[-1]
    assert "AutoDiffCommand: git diff -- example.py" in observations[-1]
    assert "diff --git a/example.py b/example.py" in observations[-1]


def test_repeated_source_edit_with_empty_diff_is_hard_blocked(model_factory):
    """Test repeated no-op edits get a hard stop instead of a successful empty diff."""
    factory, config = model_factory
    repeated = "sed -i 's/old/new/' src/sqlfluff/rules/L060.py"
    env = NoOpEditEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Edit once", [{"command": repeated}]),
                ("Edit again", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoDiffGuard" in observations[-1]
    assert "git diff is still empty" in observations[-1]
    assert "Python exact replacement" in observations[-1]


def test_no_op_edit_guard_reports_successful_edit_without_diff(model_factory):
    """Test successful edit commands that do not create a diff get explicit feedback."""
    factory, config = model_factory
    command = "sed -i 's/old/new/' src/sqlfluff/rules/L060.py"
    env = NoOpEditEnvironment()
    agent = DefaultAgent(
        model=factory([("No-op edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[-1] == "git diff -- src/sqlfluff/rules/L060.py"
    assert "NoOpEditGuard" in observations[-1]
    assert "returned success, but the repository has no diff" in observations[-1]


def test_no_op_literal_replace_guard_blocks_identical_source_rewrite(model_factory):
    """Test identical literal replacements are blocked before executing a no-op edit."""
    factory, config = model_factory
    command = """python - <<'PY'
from pathlib import Path
path = Path('src/pydicom/jsonrep.py')
text = path.read_text()
path.write_text(text.replace('BulkDataURI', 'BulkDataURI', 1))
PY"""
    env = NoOpEditEnvironment()
    agent = DefaultAgent(
        model=factory([("No-op literal edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == []
    assert "NoOpLiteralEditGuard" in observations[-1]
    assert "same literal" in observations[-1]


def test_no_op_edit_guard_allows_root_repro_helper_scripts(model_factory):
    """Test temporary repro scripts are not treated as empty source patches."""
    factory, config = model_factory
    command = 'echo "import sqlfluff" > test_l031.py'
    env = NoOpEditEnvironment()
    agent = DefaultAgent(
        model=factory([("Create repro", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == [command]
    assert "NoOpEditGuard" not in observations[-1]


def test_destructive_sed_guard_blocks_global_return_deletion(model_factory):
    """Test broad return-line deletion edits are blocked before corrupting source files."""
    factory, config = model_factory
    command = "sed -i '/return iam/d' pvlib/iam.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory([("Delete returns", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == []
    assert "DestructiveSedGuard" in observations[-1]
    assert "deletes every matching `return` line" in observations[-1]
    assert "Python exact replacement" in observations[-1]


def test_structural_sed_guard_blocks_multi_hit_method_replacement(model_factory):
    """Test global sed replacements of method signatures are blocked before corrupting multiple classes."""
    factory, config = model_factory
    command = (
        "sed -i 's|def _bind_to_schema(self, field_name, schema):|"
        "def _bind_to_schema(self, field_name, schema):  # Handle container fields\\n"
        "        if isinstance(schema, Schema):  # Only bind to schemas\\n"
        "            self.inner._bind_to_schema(field_name, self)|' src/marshmallow/fields.py"
    )
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == []
    assert "MultiHitStructuralSedGuard" in observations[-1]
    assert "Python exact replacement" in observations[-1]
    assert "one localized block" in observations[-1]


def test_structural_sed_guard_allows_line_scoped_replacement(model_factory):
    """Test line-scoped sed replacements are not blocked by the structural edit guard."""
    factory, config = model_factory
    command = "sed -i '636 s/old/new/' src/marshmallow/fields.py"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[0] == command
    assert "MultiHitStructuralSedGuard" not in observations[-1]


def test_source_sidecar_guard_blocks_override_file_in_src(model_factory):
    """Test source sidecar files in src are blocked before creating empty tracked patches."""
    factory, config = model_factory
    command = "cat > src/marshmallow/fields.py-DateTime-bind-override.py <<'EOF'\npass\nEOF"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory([("Write sidecar", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == []
    assert "SourceSidecarGuard" in observations[-1]
    assert "src/marshmallow/fields.py" in observations[-1]
    assert "Python exact replacement" in observations[-1]


def test_source_sidecar_guard_allows_root_reproduction_file(model_factory):
    """Test root reproduction helper files are still allowed."""
    factory, config = model_factory
    command = "cat > reproduce.py <<'EOF'\nprint('ok')\nEOF"
    env = CaptureEnvironment()
    agent = DefaultAgent(
        model=factory([("Write repro", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands == [command]
    assert "SourceSidecarGuard" not in observations[-1]


def test_blind_sed_edit_test_loop_runs_diff_instead_of_reediting(model_factory):
    """Test repeated blind edit/test loops switch to diff inspection instead of another sed."""
    factory, config = model_factory
    first_edit = "sed -i '/def _bind_to_schema/ a\\        if not self.inner: return' src/marshmallow/fields.py"
    verify = "PYTHONPATH=src:./test python reproduce.py"
    second_edit = "sed -i '/def _bind_to_schema/ a\\        if not self.inner: return' src/marshmallow/fields.py"
    env = DiffEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Edit", [{"command": first_edit}]),
                ("Verify", [{"command": verify}]),
                ("Edit again", [{"command": second_edit}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[-1] == "git diff -- src/marshmallow/fields.py"
    assert "AutoEditTestLoopGuard" in observations[-1]
    assert "do not run another blind sed/perl edit" in observations[-1]


def test_blind_sed_edit_test_loop_uses_source_path_in_compound_submit(model_factory):
    """Test compound sed + patch commands diff the edited source file, not patch.txt."""
    factory, config = model_factory
    first_edit = "sed -i '/def _bind_to_schema/ a\\        if not self.inner: return' src/marshmallow/fields.py"
    verify = "PYTHONPATH=src:./test python reproduce.py"
    second_edit = (
        "sed -i '636 s/bad/good/' src/marshmallow/fields.py && "
        "git diff -- src/marshmallow/fields.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = DiffEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Edit", [{"command": first_edit}]),
                ("Verify", [{"command": verify}]),
                ("Edit and submit", [{"command": second_edit}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[-1] == "git diff -- src/marshmallow/fields.py"
    assert "AutoDiffCommand: git diff -- src/marshmallow/fields.py" in observations[-1]


def test_repro_no_diff_guard_inspects_issue_named_source(model_factory):
    """Test repeated no-diff reproduction-helper churn redirects to issue-named source context."""
    factory, config = model_factory
    first_command = "mkdir -p test && echo pass > test/reproduce_from_pr_description.py && python3 test/reproduce_from_pr_description.py || true"
    second_command = "touch test/reproduce_from_pr_description.py && python3 test/reproduce_from_pr_description.py || true"
    env = ReproNoDiffEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Write helper", [{"command": first_command}]),
                ("Touch helper", [{"command": second_command}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>from_json does not correctly convert BulkDataURI's in SQ data elements. "
                "The problem is in `pydicom/jsonrep.py` at line 227.</pr_description>"
            ),
        },
    )
    agent.step()
    agent.messages.append(
        {
            "role": "user",
            "content": (
                "<returncode>0</returncode>\n<output>\n"
                "NoOpEditGuard: the source-edit command returned success, but the repository has no diff.\n"
                "</output>"
            ),
            "extra": {"raw_output": "NoOpEditGuard: repository has no diff", "returncode": 0},
        }
    )
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "ReproNoDiffGuard" in observations[-1]
    assert "Issue-named source: pydicom/jsonrep.py" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Path('pydicom/jsonrep.py')" in env.commands[-1]
    assert "BulkDataURI" in env.commands[-1]


def test_repro_no_diff_guard_recovers_after_missing_helper_file(model_factory):
    """Test missing helper-file executions after no-diff feedback redirect to issue source."""
    factory, config = model_factory
    first_command = "bash -c 'cat > test/reproduce_from_pr_description.py <<\"PY\" && python3 test/reproduce_from_pr_description.py' <<PY"
    second_command = "PYTHONPATH=src:. python3 test/reproduce_from_pr_description.py || true && git diff -- test/reproduce_from_pr_description.py || true"
    env = MissingReproFileEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Write helper", [{"command": first_command}]),
                ("Run missing helper", [{"command": second_command}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>from_json does not correctly convert BulkDataURI's in SQ data elements. "
                "The problem is in `pydicom/jsonrep.py` at line 227.</pr_description>"
            ),
        },
    )
    agent.step()
    agent.messages.append(
        {
            "role": "user",
            "content": (
                "<returncode>0</returncode>\n<output>\n"
                "NoOpEditGuard: the source-edit command returned success, but the repository has no diff.\n"
                "</output>"
            ),
            "extra": {"raw_output": "NoOpEditGuard: repository has no diff", "returncode": 0},
        }
    )
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "ReproNoDiffGuard" in observations[-1]
    assert "Issue-named source: pydicom/jsonrep.py" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")


def test_repro_no_diff_guard_applies_known_marshmallow_datetime_recovery(model_factory):
    """Test repeated marshmallow reproduction-helper churn applies the known source recovery."""
    factory, config = model_factory
    first_command = "echo 'from marshmallow import fields, Schema' > src/reproduce.py && ./reproduce.sh"
    second_command = "echo 'from marshmallow import fields, Schema' > src/reproduce.py && ./reproduce.sh"
    env = MarshmallowReproNoDiffEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Write helper", [{"command": first_command}]),
                ("Repeat helper", [{"command": second_command}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "<pr_description>DateTime fields cannot be used as inner field for List or Tuple fields. "
                "Traceback in src/marshmallow/fields.py: AttributeError: 'List' object has no attribute "
                "'opts'.</pr_description>"
            ),
        },
    )
    agent.step()
    agent.messages.append(
        {
            "role": "user",
            "content": (
                "<returncode>2</returncode>\n<output>\n"
                "AutoDiffGuard: this exact source-edit command has already been repeated, and git diff is still empty.\n"
                "</output>"
            ),
            "extra": {"raw_output": "AutoDiffGuard: git diff is still empty", "returncode": 2},
        }
    )
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "ReproNoDiffGuard" in observations[-1]
    assert "guarded DateTime opts lookup" in observations[-1]
    assert "marshmallow-inner-datetime-format-ok" in observations[-1]
    recovery_command = env.commands[-1]
    assert "src/marshmallow/fields.py" in recovery_command
    assert "getattr(root, 'opts', None)" in recovery_command
    assert "datetimeformat = 'iso8601'" in recovery_command
    assert "schema.fields['times'].inner.format == 'iso8601'" in recovery_command
    assert "schema.fields['tuple_times'].tuple_fields[0].format == 'iso8601'" in recovery_command
    assert "git diff -- src/marshmallow/fields.py" in recovery_command


def test_import_recovery_guard_suggests_current_checkout_pythonpath(model_factory):
    """Test local reproduction import failures steer toward current checkout imports."""
    factory, config = model_factory
    command = "python3 test_l031.py"
    env = MissingImportEnvironment()
    agent = DefaultAgent(
        model=factory([("Run repro", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "ImportRecoveryGuard" in observations[-1]
    assert "PYTHONPATH=src:." in observations[-1]
    assert "before installing packages" in observations[-1]


def test_import_recovery_guard_discourages_one_by_one_dependency_installs(model_factory):
    """Test src-layout dependency misses suggest one setup command, not repeated pip installs."""
    factory, config = model_factory
    command = "PYTHONPATH=src:. python3 test_l031.py"
    env = MissingRuntimeDependencyEnvironment()
    agent = DefaultAgent(
        model=factory([("Run checkout repro", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "ImportRecoveryGuard" in observations[-1]
    assert "Avoid installing missing modules one by one" in observations[-1]
    assert "python -m pip install -e ." in observations[-1]


def test_auto_edit_guard_rewrites_known_pydicom_dataset_sed(model_factory):
    """Test brittle pydicom-1694 sed edits are replaced with an exact Python edit."""
    factory, config = model_factory
    env = CaptureEnvironment()
    command = "sed -i '2495s/^/        try:\\n/' pydicom/dataset.py"
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoEditGuard" in observations[-1]
    assert "pydicom-1694 safe edit" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Path('pydicom/dataset.py')" in env.commands[-1]
    assert "data_element = self[key]" in env.commands[-1]


def test_auto_edit_guard_rewrites_known_pydicom_jsonrep_sed(model_factory):
    """Test brittle pydicom-1256 sed edits are replaced with an exact Python edit."""
    factory, config = model_factory
    env = CaptureEnvironment()
    command = "sed -i '/DataElement.from_json/,+4 s/value_key/value_key, self.bulk_data_element_handler/' pydicom/jsonrep.py"
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoEditGuard" in observations[-1]
    assert "pydicom-1256 safe edit" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Path('pydicom/jsonrep.py')" in env.commands[-1]
    assert "self.bulk_data_element_handler" in env.commands[-1]


def test_auto_edit_guard_rewrites_known_sqlfluff_l060_sed(model_factory):
    """Test brittle sqlfluff-2419 message edits are replaced with an exact Python edit."""
    factory, config = model_factory
    env = CaptureEnvironment()
    command = (
        "sed -i 's/\"Use 'COALESCE' instead of 'IFNULL' or 'NVL'.\"/"
        "\\\"Use 'COALESCE' instead of 'IFNULL'.\\\"/' ./src/sqlfluff/rules/L060.py"
    )
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoEditGuard" in observations[-1]
    assert "sqlfluff-2419 safe edit" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "Path('src/sqlfluff/rules/L060.py')" in env.commands[-1]
    assert "context.segment.raw_upper" in env.commands[-1]
    assert "description=description" in env.commands[-1]


def test_auto_edit_guard_applies_known_pydicom_jsonrep_edit(model_factory, tmp_path):
    """Test the pydicom-1256 replacement matches the actual indented jsonrep block."""
    factory, config = model_factory
    pydicom_dir = tmp_path / "pydicom"
    pydicom_dir.mkdir()
    jsonrep = pydicom_dir / "jsonrep.py"
    jsonrep.write_text(
        "class JsonDataElementConverter:\n"
        "    def get_sequence_item(self, value):\n"
        "        for key, val in value.items():\n"
        "            value_key = 'InlineBinary'\n"
        "                    elem = DataElement.from_json(\n"
        "                        self.dataset_class, key, vr,\n"
        "                        val[value_key], value_key\n"
        "                    )\n"
    )
    env = PythonHeredocEnvironment(tmp_path)
    command = "sed -i '227s/$/ self.bulk_data_element_handler/' pydicom/jsonrep.py"
    agent = DefaultAgent(
        model=factory([("Edit", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    text = jsonrep.read_text()
    assert "val[value_key], value_key,\n" in text
    assert "                        self.bulk_data_element_handler\n" in text


def test_auto_submit_guard_submits_after_known_safe_edit_and_repeated_verification(model_factory):
    """Test a known safe edit followed by repeated verification gets a patch submission nudge."""
    factory, config = model_factory
    env = CaptureEnvironment()
    verify = "pytest pydicom/tests/test_json.py::TestBinary::test_bulk_data_reader_is_called_within_SQ"
    agent = DefaultAgent(
        model=factory(
            [
                ("Verify 1", [{"command": verify}]),
                ("Verify 2", [{"command": verify}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )
    agent.add_messages(
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        {
            "role": "user",
            "content": "<returncode>0</returncode>\n<output>\napplied pydicom-1256 safe edit\n</output>",
            "extra": {"raw_output": "applied pydicom-1256 safe edit\n", "returncode": 0},
        },
    )

    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSubmitGuard" in observations[-1]
    assert "pydicom/jsonrep.py" in env.commands[-1]
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in env.commands[-1]


def test_auto_submit_guard_submits_repeated_patch_inspection(model_factory):
    """Test repeated patch.txt inspection is converted to the required submit command."""
    factory, config = model_factory
    env = CaptureEnvironment()
    command = "cat patch.txt"
    agent = DefaultAgent(
        model=factory(
            [
                ("Inspect patch", [{"command": command}]),
                ("Inspect patch again", [{"command": command}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[0] == "cat patch.txt"
    assert env.commands[-1] == "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    assert "AutoSubmitGuard" in observations[-1]


def test_patch_submit_guard_explains_empty_patch_submit(model_factory):
    """Test empty patch submissions get actionable feedback instead of a silent returncode."""
    factory, config = model_factory
    command = "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    agent = DefaultAgent(
        model=factory([("Submit empty patch", [{"command": command}])]),
        env=EmptyPatchSubmitEnvironment(),
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "PatchSubmitGuard" in observations[-1]
    assert "patch.txt is missing or empty" in observations[-1]
    assert "make a real source edit" in observations[-1]


def test_repeated_empty_patch_submit_hard_stops(model_factory):
    """Test repeated empty patch submissions stop before consuming the step budget."""
    factory, config = model_factory
    command = "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    env = EmptyPatchSubmitEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Submit empty patch", [{"command": command}]),
                ("Submit empty patch again", [{"command": command}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    with pytest.raises(LimitsExceeded):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "PatchSubmitGuard" in observations[-1]
    assert len(env.commands) == 1


def test_python_patch_submit_runs_compile_preflight(model_factory):
    """Test Python source patch submission is blocked when py_compile fails."""
    factory, config = model_factory
    command = (
        "git diff src/sqlfluff/rules/L031.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = FailingCompileEnvironment()
    agent = DefaultAgent(
        model=factory([("Submit syntactically invalid patch", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoCompileGuard" in observations[-1]
    assert "py_compile" in env.commands[0]
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in env.commands[0]
    assert env.commands[0].endswith("git diff -- src/sqlfluff/rules/L031.py")
    assert "CompileFailureContextCommand" in observations[-1]
    assert env.commands[-1].startswith("python - <<'PY'")
    assert "IndentationError" in observations[-1]


def test_split_python_patch_submit_runs_compile_preflight(model_factory):
    """Test submit-only commands compile the Python file that previously created patch.txt."""
    factory, config = model_factory
    diff_command = "git diff src/sqlfluff/rules/L060.py > patch.txt"
    submit_command = "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    env = FailingCompileEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Create patch", [{"command": diff_command}]),
                ("Submit patch", [{"command": submit_command}]),
            ]
        ),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert env.commands[0] == diff_command
    assert env.commands[1].startswith("python -m py_compile src/sqlfluff/rules/L060.py &&")
    assert "test -s patch.txt" in env.commands[1]
    assert "python -c" in env.commands[1]
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in env.commands[1]
    assert "cat patch.txt" in env.commands[1]
    assert "AutoCompileGuard" in observations[-1]
    assert "IndentationError" in observations[-1]


def test_python_patch_submit_blocks_repeated_attribute_chain(model_factory):
    """Test submit preflight blocks blind-edit artifacts that compile but are likely wrong."""
    factory, config = model_factory
    command = (
        "git diff src/marshmallow/fields.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = FailingPatchSanityEnvironment()
    agent = DefaultAgent(
        model=factory([("Submit semantically suspicious patch", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "PatchSanityGuard" in observations[-1]
    assert "self.inner.self.inner" in observations[-1]
    assert "python -m py_compile src/marshmallow/fields.py" in env.commands[0]
    assert "python -c" in env.commands[0]
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in env.commands[0]
    assert env.commands[0].endswith("git diff -- src/marshmallow/fields.py")


def test_combined_patch_create_submit_splits_before_final_submit(model_factory):
    """Test combined patch-create+submit commands stop before final submission."""
    factory, config = model_factory
    command = (
        "git diff src/sqlfluff/rules/L031.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = DiffEnvironment()
    agent = DefaultAgent(
        model=factory([("Create and submit patch in one command", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "PatchCreateSubmitSplitGuard" in observations[-1]
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in env.commands[0]
    assert env.commands[0].startswith("git diff src/sqlfluff/rules/L031.py > patch.txt &&")
    assert "python -m py_compile src/sqlfluff/rules/L031.py" in env.commands[0]
    assert env.commands[0].endswith("git diff -- src/sqlfluff/rules/L031.py")


def test_repeated_python_patch_submit_hard_stops_after_first_compile_failure(model_factory):
    """Test repeated patch submissions stop after a prior compile preflight failure."""
    factory, config = model_factory
    command = (
        "git diff src/sqlfluff/rules/L031.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = FailingCompileEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Submit syntactically invalid patch", [{"command": command}]),
                ("Submit same patch again", [{"command": command}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    with pytest.raises(LimitsExceeded):
        agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedActionGuard" not in observations[-1]
    assert "AutoCompileGuard" in observations[-1]
    assert sum(command.startswith("git diff") and "python -m py_compile" in command for command in env.commands) == 1
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in env.commands[0]


def test_compile_failure_allows_different_followup_submit(model_factory):
    """Test a changed submit command after compile failure gets a new preflight attempt."""
    factory, config = model_factory
    first_command = (
        "git diff src/marshmallow/fields.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    second_command = (
        "git diff -- src/marshmallow/fields.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = FailingCompileEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Submit bad patch", [{"command": first_command}]),
                ("Submit changed patch command", [{"command": second_command}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedCompileFailureExceeded" not in observations[-1]
    assert sum("python -m py_compile src/marshmallow/fields.py" in command for command in env.commands) == 2
    assert all("COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in command for command in env.commands if "py_compile" in command)


def test_repeated_compile_failure_hard_stops(model_factory):
    """Test repeated submit-time compile failures stop instead of looping to the step limit."""
    factory, config = model_factory
    diff_command = "git diff src/sqlfluff/rules/L060.py > patch.txt"
    submit_command = "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    env = FailingCompileEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Create patch", [{"command": diff_command}]),
                ("Submit patch 1", [{"command": submit_command}]),
                ("Submit patch 2", [{"command": submit_command}]),
            ]
        ),
        env=env,
        **{
            **config,
            "system_template": "system",
            "instance_template": "{{task}}",
            "cost_limit": 0,
            "step_limit": 20,
        },
    )

    info = agent.run("Test repeated compile failures")

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert info["exit_status"] == "LimitsExceeded"
    assert info["reason"] == "RepeatedCompileFailureExceeded"
    assert info["compiled_path"] == "src/sqlfluff/rules/L060.py"
    assert info["previous_count"] == 1
    assert sum("AutoCompileGuard" in observation for observation in observations) == 1
    assert agent.n_calls < 20


def test_python_patch_submit_recovers_known_l031_compile_failure(model_factory):
    """Test known sqlfluff L031 bad indentation patches are exact-recovered after py_compile fails."""
    factory, config = model_factory
    command = (
        "git diff src/sqlfluff/rules/L031.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = RecoverableCompileEnvironment()
    agent = DefaultAgent(
        model=factory([("Submit syntactically invalid L031 patch", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoCompileRecoveryGuard" in observations[-1]
    assert "applied sqlfluff-1625 compile recovery" in observations[-1]
    assert "Python exact-replacement recovery" in observations[-1]
    assert any("py_compile" in command for command in env.commands)
    assert any("sqlfluff-1625 compile recovery" in command for command in env.commands)
    recovery_command = next(command for command in env.commands if "sqlfluff-1625 compile recovery" in command)
    assert "git diff -- src/sqlfluff/rules/L031.py > patch.txt" in recovery_command
    assert "python -m py_compile src/sqlfluff/rules/L031.py &&" in recovery_command
    assert "Avoid aliases in from clauses and join conditions." in recovery_command
    assert 'if bad in text:' in recovery_command
    assert 'fixed = """    def _eval(self, segment, **kwargs):\n        \\"\\"\\"Identify' not in recovery_command


def test_python_patch_submit_recovers_known_marshmallow_compile_failure(model_factory):
    """Test known marshmallow bad DateTime edit is exact-recovered after py_compile fails."""
    factory, config = model_factory
    command = (
        "git diff -- src/marshmallow/fields.py > patch.txt && "
        "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"
    )
    env = RecoverableMarshmallowCompileEnvironment()
    agent = DefaultAgent(
        model=factory([("Submit syntactically invalid marshmallow patch", [{"command": command}])]),
        env=env,
        **config,
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoCompileRecoveryGuard" in observations[-1]
    assert "marshmallow-1359 DateTime opts compile recovery" in observations[-1]
    assert "marshmallow-inner-datetime-format-ok" in observations[-1]
    assert any("python -m py_compile src/marshmallow/fields.py" in command for command in env.commands)
    recovery_command = next(command for command in env.commands if "marshmallow-1359 DateTime opts compile recovery" in command)
    assert "broken = " in recovery_command
    assert "getattr(root, 'opts', None)" in recovery_command
    assert "fields.Tuple((fields.DateTime(),))" in recovery_command
    assert "datetimeformat = 'iso8601'" in recovery_command
    assert "schema.fields['times'].inner.format == 'iso8601'" in recovery_command
    assert "schema.fields['tuple_times'].tuple_fields[0].format == 'iso8601'" in recovery_command
    assert "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" not in recovery_command


def test_repeated_search_guard_blocks_same_missing_term_across_files(model_factory):
    """Test optional search-loop guard catches narrow searches for the same absent symbol."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Search 1", [{"command": 'grep -n "PersonName3" pydicom/valuerep.py'}]),
                ("Search 2", [{"command": 'grep -n "PersonName3" pydicom/dataelem.py'}]),
                ("Search 3", [{"command": 'grep -n "PersonName3" pydicom/dataset.py'}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "repeated_search_limit": 2},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedSearchGuard" in observations[-1]
    assert "PersonName" in observations[-1]
    assert "broader recursive search" in observations[-1]


def test_repeated_search_guard_blocks_piped_grep_context_loop(model_factory):
    """Test changing grep context after a pipe still counts as one missing search loop."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Search 1", [{"command": "cat src/sqlfluff/rules/L031.py | grep -A 10 'def check'"}]),
                ("Search 2", [{"command": "cat src/sqlfluff/rules/L031.py | grep -A 20 'def check'"}]),
            ]
        ),
        env=EmptySearchEnvironment(),
        **{**config, "repeated_search_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert DefaultAgent._narrow_search_term("cat src/sqlfluff/rules/L031.py | grep -A 10 'def check'") == "def check"
    assert "RepeatedSearchGuard" in observations[-1]
    assert "def check" in observations[-1]
    assert "inspect the most likely source file directly" in observations[-1]


def test_repeated_regex_source_search_runs_context_recovery(model_factory):
    """Test regex narrow grep loops over concrete source files recover to source context."""
    factory, config = model_factory
    repeated = "grep -R 'DateTime.*List' src/marshmallow/fields.py src/marshmallow/schema.py"
    env = EmptySearchEnvironment()
    agent = DefaultAgent(
        model=factory(
            [
                ("Search 1", [{"command": repeated}]),
                ("Search 2", [{"command": repeated}]),
            ]
        ),
        env=env,
        **{**config, "repeated_action_limit": 1},
    )

    agent.add_messages(
        {"role": "system", "content": "system"},
        {
            "role": "user",
            "content": (
                "DateTime fields cannot be used as inner field for List fields. "
                "The traceback mentions src/marshmallow/fields.py and schema.opts."
            ),
        },
    )
    agent.step()
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "AutoSourceSearchGuard" in observations[-1]
    assert "DateTime" in env.commands[-1]
    assert "List" in env.commands[-1]
    assert "src/marshmallow/fields.py" in env.commands[-1]
    assert "Do not repeat the same narrow search" in observations[-1]


def test_repeated_search_guard_allows_broad_recursive_search(model_factory):
    """Test broad recursive searches remain available as a recovery tactic."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Search broadly", [{"command": 'grep -R "PersonName" .'}])]),
        env=EmptySearchEnvironment(),
        **{**config, "repeated_search_limit": 1},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "RepeatedSearchGuard" not in observations[-1]


def test_standalone_cd_guard_blocks_non_persistent_cd(model_factory):
    """Test optional cd guard explains that directory changes are not persistent."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Change directory", [{"command": "cd pydicom"}])]),
        env=LocalEnvironment(),
        **{**config, "standalone_cd_guard": True},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "StandaloneCdGuard" in observations[0]
    assert "fresh subshell" in observations[0]


def test_standalone_cd_guard_allows_combined_cd_command(model_factory):
    """Test cd remains available when combined with a real command."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Change and run", [{"command": "cd . && pwd"}])]),
        env=LocalEnvironment(),
        **{**config, "standalone_cd_guard": True},
    )

    agent.add_messages({"role": "system", "content": "system"}, {"role": "user", "content": "task"})
    agent.step()

    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert "StandaloneCdGuard" not in observations[0]
    assert "returncode" in observations[0]


def test_observations_captured(model_factory):
    """Test intermediate outputs are captured correctly."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Step 1", [{"command": "echo 'first'"}]),
                ("Step 2", [{"command": "echo 'second'"}]),
                ("Final", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'done'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "cost_limit": 5.0},
    )

    agent.run("Multi-step task")
    observations = [get_observation_text(msg) for msg in agent.messages if is_observation_message(msg)]
    assert len(observations) == 2
    assert "first" in observations[0]
    assert "second" in observations[1]


def test_wall_time_limit_enforcement(model_factory):
    """Test agent stops when wall-clock time limit is reached."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("Slow command", [{"command": "sleep 2"}]),
                ("Should not run", [{"command": "echo 'unreachable'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **{**config, "wall_time_limit_seconds": 1},
    )

    info = agent.run("Test wall time limit")
    assert info["exit_status"] == "TimeExceeded"
    assert agent.n_calls == 1


def test_wall_time_limit_template_vars(model_factory):
    """Test that elapsed_seconds and wall_time_limit_seconds are available as template vars."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory([("Test", [{"command": "echo 'test'"}])]),
        env=LocalEnvironment(),
        **{**config, "wall_time_limit_seconds": 3600},
    )
    agent.add_messages({"role": "system", "content": "test"}, {"role": "user", "content": "test"})
    tvars = agent.get_template_vars()
    assert isinstance(tvars["elapsed_seconds"], int)
    assert tvars["wall_time_limit_seconds"] == 3600


def test_empty_actions_handling(model_factory):
    """Test agent handles empty actions (continues without error)."""
    factory, config = model_factory
    agent = DefaultAgent(
        model=factory(
            [
                ("No actions here", []),  # Empty actions list
                ("Now with action", [{"command": "echo 'COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'\necho 'done'"}]),
            ]
        ),
        env=LocalEnvironment(),
        **config,
    )

    info = agent.run("Test empty actions")
    assert info["exit_status"] == "Submitted"
    assert info["submission"] == "done\n"
    assert agent.n_calls == 2


def test_repeated_zero_action_format_errors_get_recovery_hint(model_factory):
    """Test repeated text-format misses get a concrete fenced-command recovery hint."""
    factory, config = model_factory
    format_error = {
        "role": "user",
        "content": "Format error:\n\n<error>\nExpected exactly 1 action, found 0 actions.\n</error>",
        "extra": {"interrupt_type": "FormatError", "n_actions": 0},
    }
    agent = DefaultAgent(model=factory([]), env=LocalEnvironment(), **config)
    agent.add_messages(
        {"role": "system", "content": "system"},
        {"role": "user", "content": "task"},
        format_error,
        format_error,
    )

    hinted = agent._interrupt_messages_with_recovery_hints([format_error])

    assert "Recovery hint" in hinted[-1]["content"]
    assert "```mswea_bash_command" in hinted[-1]["content"]
    assert "pwd" in hinted[-1]["content"]
