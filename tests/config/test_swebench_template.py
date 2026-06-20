from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import StrictUndefined, Template

from minisweagent.agents.default import AgentConfig


@dataclass
class MockOutput:
    """Mock output object for testing the template"""

    returncode: int
    output: str
    exception_info: str = ""


def test_observation_template_short_output():
    """Test that short output (< 10000 chars) is displayed in full"""
    # Load the swebench config
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Create mock output with short content
    output = MockOutput(returncode=0, output="Success! Operation completed.\nWarning: minor issue")

    # Render the template
    result = template.render(output=output)

    # Verify the result contains all parts and no truncation
    assert "<returncode>" in result
    assert "0" in result
    assert "<output>" in result
    assert "Success! Operation completed." in result
    assert "Warning: minor issue" in result

    # Should not contain truncation elements for short output
    assert "<output_head>" not in result
    assert "<elided_chars>" not in result
    assert "<output_tail>" not in result
    assert "<warning>" not in result


def test_observation_template_long_output():
    """Test that long output (> 10000 chars) is truncated with head/tail format"""
    # Load the swebench config
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Create mock output with long content
    long_output = "A" * 8000 + "B" * 3000  # 11000 characters total
    # Total will be > 10000 chars

    output = MockOutput(returncode=1, output=long_output)

    # Render the template
    result = template.render(output=output)

    # Should contain truncation elements for long output
    assert "<warning>" in result
    assert "The output of your last command was too long" in result
    assert "<output_head>" in result
    assert "<elided_chars>" in result
    assert "characters elided" in result
    assert "<output_tail>" in result

    # Should still contain the basic structure
    assert "<returncode>" in result
    assert "1" in result

    # Verify the head contains first part of output
    head_start = result.find("<output_head>")
    head_end = result.find("</output_head>")
    head_content = result[head_start:head_end]
    assert "AAAA" in head_content  # Should contain start of output

    # Verify the tail contains last part of output
    tail_start = result.find("<output_tail>")
    tail_end = result.find("</output_tail>")
    tail_content = result[tail_start:tail_end]
    assert "BBBB" in tail_content  # Should contain end of output


def test_observation_template_edge_case_exactly_10000_chars():
    """Test the boundary case where output is around 10000 characters"""
    # Load the swebench config
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Use a large amount of data that will definitely exceed 10000 chars when rendered
    output = MockOutput(returncode=0, output="X" * 10000)

    # Render the template
    result = template.render(output=output)

    # Should use truncated format for large output
    assert "<output_head>" in result
    assert "<elided_chars>" in result
    assert "<output_tail>" in result
    assert "<warning>" in result
    # The X's should still be present in head or tail
    assert "XXXX" in result


def test_observation_template_just_under_10000_chars():
    """Test that smaller output shows full output without truncation"""
    # Load the swebench config
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract the template (now in model section)
    template_str = config["model"]["observation_template"]
    template = Template(template_str, undefined=StrictUndefined)

    # Use a reasonably sized output that should be well under 10000 chars when rendered
    output = MockOutput(returncode=0, output="Y" * 8000)

    # Render the template
    result = template.render(output=output)

    # Should show full output without truncation
    assert "<output_head>" not in result
    assert "<elided_chars>" not in result
    assert "<output_tail>" not in result
    assert "<warning>" not in result
    assert "Y" * 8000 in result


def test_agent_config_requires_templates():
    """Test that AgentConfig now requires all template fields (no defaults in code)"""
    import pytest
    from pydantic import ValidationError

    # AgentConfig should require all template fields now (Pydantic raises ValidationError)
    with pytest.raises(ValidationError, match="validation error"):
        AgentConfig()


def test_swebench_prompt_keeps_action_visible_early():
    """The local text parser only sees actions after the model finishes."""
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["system_template"] + "\n" + config["agent"]["instance_template"]
    assert "one short sentence" in prompt
    assert "25 words or fewer" in prompt
    assert "Put the command block immediately after THOUGHT" in prompt
    assert "action is visible early" in prompt


def test_swebench_prompt_discourages_repeated_failed_searches():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "do not repeat the same command with only a larger context number" in prompt
    assert "Switch evidence strategies" in prompt
    assert "sed -n" in prompt


def test_swebench_prompt_prefers_current_checkout_reproductions():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "PYTHONPATH=src:." in prompt
    assert "current checkout" in prompt
    assert "Do not use `pip install <package-under-repair>`" in prompt


def test_swebench_prompt_discourages_truncated_inline_edits():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "Editing Discipline" in prompt
    assert "closing code fence will not be truncated" in prompt
    assert "Python exact-replacement script" in prompt
    assert "instead of emitting a long inline `sed -i` command" in prompt


def test_swebench_prompt_commits_to_edit_after_source_context():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "Once you have inspected the relevant source context" in prompt
    assert "do not keep running read-only source parse or path checks" in prompt
    assert "one short exact-replacement source edit" in prompt
    assert "resolved full path" in prompt


def test_swebench_prompt_handles_missing_reproduction_artifacts():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "reproduction script or data file is missing" in prompt
    assert "do not rerun the absent script" in prompt
    assert "find . -iname '<name-or-pattern>'" in prompt
    assert "grep -R '<issue-term>' <likely-dir>" in prompt


def test_swebench_prompt_requires_source_inspection_before_empty_submit():
    config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "minisweagent"
        / "config"
        / "benchmarks"
        / "swebench_backticks.yaml"
    )
    with open(config_path) as f:
        config = yaml.safe_load(f)

    prompt = config["agent"]["instance_template"]
    assert "issue text names a source file" in prompt
    assert "inspect that current source location before creating or submitting a patch" in prompt
    assert "patch.txt` is missing/empty" in prompt
    assert "Make a real source edit first" in prompt
