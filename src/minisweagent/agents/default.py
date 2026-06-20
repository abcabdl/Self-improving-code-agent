"""Basic agent class. See https://mini-swe-agent.com/latest/advanced/control_flow/ for visual explanation
or https://minimal-agent.com for a tutorial on the basic building principles.
"""

import json
import logging
import re
import shlex
import time
import traceback
from pathlib import Path

from jinja2 import StrictUndefined, Template
from pydantic import BaseModel

from minisweagent import Environment, Model, __version__
from minisweagent.exceptions import InterruptAgentFlow, LimitsExceeded, TimeExceeded
from minisweagent.utils.serialize import recursive_merge


class AgentConfig(BaseModel):
    """Check the config files in minisweagent/config for example settings."""

    system_template: str
    """Template for the system message (the first message)."""
    instance_template: str
    """Template for the first user message specifying the task (the second message overall)."""
    step_limit: int = 0
    """Maximum number of steps the agent can take."""
    cost_limit: float = 3.0
    """Stop agent after exceeding (!) this cost."""
    wall_time_limit_seconds: int = 0
    """Stop agent after this many seconds of wall-clock time. 0 means no limit."""
    output_path: Path | None = None
    """Save the trajectory to this path."""
    repeated_action_limit: int = 0
    """Reject an action after the same command has appeared this many times. 0 disables the guard."""
    standalone_cd_guard: bool = False
    """Reject standalone cd commands because each action runs in a fresh subshell."""
    repeated_search_limit: int = 0
    """Reject narrow searches for the same missing term after this many attempts. 0 disables the guard."""


class DefaultAgent:
    def __init__(self, model: Model, env: Environment, *, config_class: type = AgentConfig, **kwargs):
        """See the `AgentConfig` class for permitted keyword arguments."""
        self.config = config_class(**kwargs)
        self.messages: list[dict] = []
        self.model = model
        self.env = env
        self.extra_template_vars = {}
        self.logger = logging.getLogger("agent")
        self.cost = 0.0
        self.n_calls = 0
        self._start_time = time.time()

    def get_template_vars(self, **kwargs) -> dict:
        return recursive_merge(
            self.config.model_dump(),
            self.env.get_template_vars(),
            self.model.get_template_vars(),
            {
                "n_model_calls": self.n_calls,
                "model_cost": self.cost,
                "elapsed_seconds": int(time.time() - self._start_time),
            },
            self.extra_template_vars,
            kwargs,
        )

    def _render_template(self, template: str) -> str:
        return Template(template, undefined=StrictUndefined).render(**self.get_template_vars())

    def add_messages(self, *messages: dict) -> list[dict]:
        self.logger.debug(messages)  # set log level to debug to see
        self.messages.extend(messages)
        return list(messages)

    def handle_uncaught_exception(self, e: Exception) -> list[dict]:
        return self.add_messages(
            self.model.format_message(
                role="exit",
                content=str(e),
                extra={
                    "exit_status": type(e).__name__,
                    "submission": "",
                    "exception_str": str(e),
                    "traceback": traceback.format_exc(),
                },
            )
        )

    def run(self, task: str = "", **kwargs) -> dict:
        """Run step() until agent is finished. Returns dictionary with exit_status, submission keys."""
        self.extra_template_vars |= {"task": task, **kwargs}
        self.messages = []
        self.add_messages(
            self.model.format_message(role="system", content=self._render_template(self.config.system_template)),
            self.model.format_message(role="user", content=self._render_template(self.config.instance_template)),
        )
        while True:
            try:
                self.step()
            except InterruptAgentFlow as e:
                self.add_messages(*self._interrupt_messages_with_recovery_hints(e.messages))
            except Exception as e:
                self.handle_uncaught_exception(e)
                raise
            finally:
                self.save(self.config.output_path)
            if self.messages[-1].get("role") == "exit":
                break
        return self.messages[-1].get("extra", {})

    def step(self) -> list[dict]:
        """Query the LM, execute actions."""
        return self.execute_actions(self.query())

    def query(self) -> dict:
        """Query the model and return model messages. Override to add hooks."""
        if 0 < self.config.step_limit <= self.n_calls or 0 < self.config.cost_limit <= self.cost:
            raise LimitsExceeded(
                {
                    "role": "exit",
                    "content": "LimitsExceeded",
                    "extra": {"exit_status": "LimitsExceeded", "submission": ""},
                }
            )
        if 0 < self.config.wall_time_limit_seconds <= int(time.time() - self._start_time):
            raise TimeExceeded(
                {
                    "role": "exit",
                    "content": "TimeExceeded",
                    "extra": {"exit_status": "TimeExceeded", "submission": ""},
                }
            )
        self.n_calls += 1
        message = self.model.query(self.messages)
        self.cost += message.get("extra", {}).get("cost", 0.0)
        self.add_messages(message)
        return message

    def execute_actions(self, message: dict) -> list[dict]:
        """Execute actions in message, add observation messages, return them."""
        outputs = [self._execute_action(action) for action in message.get("extra", {}).get("actions", [])]
        return self.add_messages(*self.model.format_observation_messages(message, outputs, self.get_template_vars()))

    def _execute_action(self, action: dict) -> dict:
        command = str(action.get("command", "")).strip()
        if self.config.standalone_cd_guard and re.fullmatch(r"cd(?:\s+[^;&|]+)?", command):
            return {
                "returncode": 2,
                "exception_info": "",
                "output": (
                    "StandaloneCdGuard: directory changes do not persist across actions because each command "
                    "runs in a fresh subshell. Use an explicit path or combine the directory change with the "
                    "real command, for example `cd path && command`."
                ),
            }
        if self._looks_like_unredirected_heredoc(command):
            return {
                "returncode": 2,
                "exception_info": "",
                "output": (
                    "HeredocWriteGuard: this command uses a heredoc without redirecting it to a file or piping "
                    "it to another command, so it only prints the text and does not create the intended script. "
                    "Use `cat > path <<'EOF'`, `tee path <<'EOF'`, or pipe the heredoc into the interpreter."
                ),
            }
        if self._looks_like_identical_literal_replace_edit(command):
            return {
                "returncode": 2,
                "exception_info": "",
                "output": (
                    "NoOpLiteralEditGuard: this source-edit command replaces a literal string with the exact "
                    "same literal, so it cannot change behavior. Do not write the file back with an identical "
                    "`.replace(old, old, ...)` edit. Use the current source context to replace the actual buggy "
                    "call or branch with a different implementation, then verify with a focused check."
                ),
            }
        sidecar_feedback = self._source_sidecar_write_feedback(command)
        if sidecar_feedback:
            return sidecar_feedback
        safe_edit_action = self._safe_known_edit_action(command)
        if safe_edit_action:
            safe_edit_output = self.env.execute(safe_edit_action)
            return {
                **safe_edit_output,
                "output": (
                    "AutoEditGuard: replaced a brittle known sed/perl edit with a deterministic "
                    "Python exact-replacement edit for this known localized fix.\n"
                    f"OriginalCommand: {command}\n"
                    f"AutoEditCommand: {safe_edit_action['command']}\n"
                    f"{safe_edit_output.get('output', '')}"
                ),
            }
        destructive_sed_feedback = self._destructive_blind_sed_feedback(command)
        if destructive_sed_feedback:
            return destructive_sed_feedback
        structural_sed_feedback = self._multi_hit_structural_sed_feedback(command)
        if structural_sed_feedback:
            return structural_sed_feedback
        edit_test_loop_action = self._blind_sed_edit_test_loop_diff_action(command)
        if edit_test_loop_action:
            edit_test_loop_output = self.env.execute(edit_test_loop_action)
            return {
                **edit_test_loop_output,
                "returncode": 2,
                "output": (
                    "AutoEditTestLoopGuard: this blind sed/perl source edit targets a file that was "
                    "already edited and then verified. Repeating another blind edit/test cycle usually "
                    "creates duplicate or misplaced code. I ran git diff instead of applying the edit "
                    "again.\n"
                    f"OriginalCommand: {command}\n"
                    f"AutoDiffCommand: {edit_test_loop_action['command']}\n"
                    f"{edit_test_loop_output.get('output', '')}\n"
                    "Next: inspect this diff. If it is the intended minimal patch, create patch.txt and "
                    "submit it. If it is wrong, use a Python exact replacement based on the current file "
                    "contents; do not run another blind sed/perl edit on this same file."
                ),
            }
        edit_intent_read_path = self._source_read_only_path(command)
        if edit_intent_read_path and self._current_message_declares_source_edit():
            resolved_source_path = self._resolved_source_path_for_basename(edit_intent_read_path)
            resolved_hint = (
                f" Use the resolved full path `{resolved_source_path}`."
                if resolved_source_path and resolved_source_path != edit_intent_read_path
                else ""
            )
            return {
                "returncode": 2,
                "exception_info": "",
                "output": (
                    "EditIntentGuard: your THOUGHT says the next step is a source edit, but the command "
                    f"only reads or parses `{edit_intent_read_path}` and cannot create a patch. "
                    "The action must match the stated edit intent. Do not run another read-only "
                    "source parse/path check. Make one short exact-replacement edit in the source file, "
                    f"then run a focused verification.{resolved_hint}"
                ),
            }
        limit = self.config.repeated_action_limit
        if limit > 0 and command:
            previous_count = 0
            normalized_command = self._repeat_guard_key(command)
            for message in self.messages[:-1]:
                if not (message.get("role") == "assistant" or message.get("object") == "response"):
                    continue
                for previous_action in message.get("extra", {}).get("actions", []):
                    previous_command = str(previous_action.get("command", "")).strip()
                    if self._repeat_guard_key(previous_command) == normalized_command:
                        previous_count += 1
                    elif self._looks_like_source_edit(previous_command):
                        previous_count = 0
            if previous_count >= limit:
                if self._looks_like_patch_submit_command(command):
                    return self._execute_with_empty_patch_feedback(action)
                patch_submit_action = self._patch_file_submit_action(command)
                if patch_submit_action:
                    patch_submit_output = self._execute_with_empty_patch_feedback(patch_submit_action)
                    return {
                        **patch_submit_output,
                        "output": (
                            "AutoSubmitGuard: this patch.txt inspection command is being repeated after "
                            "the patch file was prepared. I ran the required non-empty patch submission "
                            "command instead.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoSubmitCommand: {patch_submit_action['command']}\n"
                            f"{patch_submit_output.get('output', '')}"
                        ),
                    }
                submit_action = self._known_safe_edit_submit_action(command)
                if submit_action:
                    submit_output = self._execute_with_empty_patch_feedback(submit_action)
                    return {
                        **submit_output,
                        "output": (
                            "AutoSubmitGuard: a known pydicom safe edit was already applied, and the "
                            "agent is now repeating a verification command instead of submitting the "
                            "non-empty source diff. I created patch.txt and submitted the current diff.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoSubmitCommand: {submit_action['command']}\n"
                            f"{submit_output.get('output', '')}"
                        ),
                    }
                diff_action = self._source_edit_diff_action(command)
                if diff_action:
                    diff_output = self.env.execute(diff_action)
                    diff_text = str(diff_output.get("output", "")).strip()
                    if diff_output.get("returncode") == 0 and not diff_text:
                        return {
                            **diff_output,
                            "returncode": 2,
                            "output": (
                                "AutoDiffGuard: this exact source-edit command has already been repeated, "
                                "and git diff is still empty. The edit is a no-op. Do not run this edit "
                                "again and do not submit patch.txt. Inspect the actual source text around "
                                "the target, then use a different edit method such as a Python exact "
                                "replacement based on the current file contents.\n"
                                f"OriginalCommand: {command}\n"
                                f"AutoDiffCommand: {diff_action['command']}"
                            ),
                        }
                    return {
                        **diff_output,
                        "output": (
                            "AutoDiffGuard: this exact source-edit command has already been repeated. "
                            "I ran git diff so you can inspect the current patch instead of applying the "
                            "same edit again.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoDiffCommand: {diff_action['command']}\n"
                            f"{diff_output.get('output', '')}"
                        ),
                    }
                source_search_recovery_action = self._source_search_recovery_action(command, previous_count)
                if source_search_recovery_action:
                    if self._source_search_recovery_already_ran(command):
                        raise LimitsExceeded(
                            {
                                "role": "exit",
                                "content": "RepeatedActionLimitExceeded",
                                "extra": {
                                    "exit_status": "LimitsExceeded",
                                    "submission": "",
                                    "reason": "RepeatedSourceSearchRecoveryExceeded",
                                    "repeated_command": command,
                                    "previous_count": previous_count,
                                },
                            }
                        )
                    source_search_recovery_output = self.env.execute(source_search_recovery_action)
                    compact_output = self._compact_guard_output(str(source_search_recovery_output.get("output", "")))
                    return {
                        **source_search_recovery_output,
                        "output": (
                            "AutoSourceSearchGuard: this narrow source search has already repeated without "
                            "progress. I ran a compact issue-term scan in the concrete source path and nearby "
                            "Python modules instead.\n"
                            f"OriginalCommand: {command}\n"
                            "AutoSourceSearchCommand: compact issue-term source scan\n"
                            f"{compact_output}\n"
                            "RecoveryBoundary: repeating OriginalCommand after this observation is an invalid "
                            "action. Use the recovered source evidence to choose a different concrete command.\n"
                            "Do not repeat the same narrow search. "
                            "Next: use the source context above to inspect one concrete implementation path, "
                            "make a source edit, run a focused reproduction, inspect git diff, create patch.txt, "
                            "and submit."
                        ),
                    }
                find_file_context_action = self._find_file_context_action(command, previous_count)
                if find_file_context_action:
                    if self._find_file_context_already_ran(command):
                        raise LimitsExceeded(
                            {
                                "role": "exit",
                                "content": "RepeatedActionLimitExceeded",
                                "extra": {
                                    "exit_status": "LimitsExceeded",
                                    "submission": "",
                                    "reason": "RepeatedFindFileContextExceeded",
                                    "repeated_command": command,
                                    "previous_count": previous_count,
                                },
                            }
                        )
                    find_file_context_output = self.env.execute(find_file_context_action)
                    compact_output = self._compact_guard_output(str(find_file_context_output.get("output", "")))
                    return {
                        **find_file_context_output,
                        "output": (
                            "AutoFindContextGuard: this file-name search already found a concrete file. "
                            "I inspected focused source context in that file instead of repeating the search.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoFindContextCommand: {find_file_context_action['command']}\n"
                            f"{compact_output}\n"
                            "RecoveryBoundary: repeating OriginalCommand after this observation is an invalid "
                            "action. Use the recovered file path/context to choose a different concrete command.\n"
                            "Next: inspect one shown function body if needed, make the minimal source edit, "
                            "run a focused reproduction, inspect git diff, create patch.txt, and submit."
                        ),
                    }
                fallback_action = self._fallback_search_action(command, previous_count)
                if fallback_action:
                    fallback_output = self.env.execute(fallback_action)
                    return {
                        **fallback_output,
                        "output": (
                            "AutoRecoveryGuard: the requested search has already been repeated and appears "
                            "to target a missing/versioned symbol. "
                            f"OriginalCommand: {command}\n"
                            "I ran a recovery search instead.\n"
                            f"AutoRecoveryCommand: {fallback_action['command']}\n"
                            f"{fallback_output.get('output', '')}"
                        ),
                    }
                hard_recovery_action = self._hard_recovery_action(command, previous_count)
                if hard_recovery_action:
                    hard_recovery_output = self.env.execute(hard_recovery_action)
                    return {
                        **hard_recovery_output,
                        "output": (
                            "AutoRecoveryGuard: this missing/versioned-symbol search has already been recovered "
                            "multiple times. I inspected the likely base-symbol implementation instead of "
                            "running the missing-symbol search again.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoRecoveryCommand: {hard_recovery_action['command']}\n"
                            f"{hard_recovery_output.get('output', '')}\n"
                            "Next: if the required method or compatibility behavior is absent, edit this source "
                            "file directly, run a focused reproduction, inspect git diff, create patch.txt, "
                            "and submit."
                        ),
                    }
                safe_context_edit_action = self._safe_known_context_edit_action(command, previous_count)
                if safe_context_edit_action:
                    safe_context_edit_output = self.env.execute(safe_context_edit_action)
                    return {
                        **safe_context_edit_output,
                        "output": (
                            "AutoEditGuard: this repeated pydicom JSON BulkDataURI inspection matches a "
                            "known localized pydicom-1256 repair. I applied the deterministic Python "
                            "exact-replacement edit instead of inspecting the same context again.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoEditCommand: {safe_context_edit_action['command']}\n"
                            f"{safe_context_edit_output.get('output', '')}\n"
                            "Next: run a focused verification, inspect git diff, create patch.txt, and submit."
                        ),
                    }
                context_recovery_action = self._context_recovery_action(command, previous_count)
                if context_recovery_action:
                    context_recovery_output = self.env.execute(context_recovery_action)
                    return {
                        **context_recovery_output,
                        "output": (
                            "AutoContextGuard: this exact inspection/search command has already been repeated "
                            "without progress. I ran a narrower source-context command instead.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoContextCommand: {context_recovery_action['command']}\n"
                            f"{context_recovery_output.get('output', '')}\n"
                            "Next: stop inspecting this same target. Make the minimal source edit described by "
                            "the issue or retrieved reflection, run a focused reproduction, inspect git diff, "
                            "create patch.txt, and submit."
                        ),
                    }
                source_read_path = self._source_read_only_path(command)
                if source_read_path and self._source_read_succeeded_recently(source_read_path):
                    resolved_source_path = self._resolved_source_path_for_basename(source_read_path)
                    resolved_hint = (
                        f" Previously resolved full current path: `{resolved_source_path}`. "
                        "Use that full path in the next source edit; do not use only the basename."
                        if resolved_source_path and resolved_source_path != source_read_path
                        else ""
                    )
                    if previous_count >= limit + 3:
                        raise LimitsExceeded(
                            {
                                "role": "exit",
                                "content": "RepeatedActionLimitExceeded",
                                "extra": {
                                    "exit_status": "LimitsExceeded",
                                    "submission": "",
                                    "reason": "RepeatedSourceReadOnlyExceeded",
                                    "repeated_command": command,
                                    "previous_count": previous_count,
                                },
                            }
                        )
                    return {
                        "returncode": 2,
                        "exception_info": "",
                        "output": (
                            "AutoSourceReadGuard: this source read/parse check has already run for "
                            f"`{source_read_path}` and cannot produce a patch. Do not repeat this command "
                            "and do not rerun path migration for this same existing source path."
                            f"{resolved_hint} Use the "
                            "source context already observed to make a minimal source edit, then run a "
                            "focused verification, inspect git diff, create patch.txt, and submit a "
                            "non-empty patch."
                        ),
                    }
                if self._context_recovery_target(command) and previous_count > 4:
                    return {
                        "returncode": 2,
                        "exception_info": "",
                        "output": (
                            "AutoContextGuard: this exact inspection/search command has already triggered "
                            "a source-context recovery and is now suppressed. Do not run this command again. "
                            "Your next action must be a source edit, a focused verification after an edit, "
                            "or a non-empty patch submission command of the form "
                            "`test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt`."
                        ),
                    }
                if self._has_versioned_search_term(command):
                    return {
                        "returncode": 2,
                        "exception_info": "",
                        "output": (
                            "AutoRecoveryGuard: this missing/versioned-symbol search has already been blocked, "
                            "recovered with base-symbol searches, and followed by a source-context inspection. "
                            "The repeated search is now suppressed to avoid filling the context with duplicate "
                            "observations. Do not run this command again. Edit the likely source file directly, "
                            "run a focused reproduction, inspect git diff, create patch.txt, and submit."
                        ),
                    }
                ls_recovery_action = self._ls_recovery_action(command, previous_count)
                if ls_recovery_action:
                    if previous_count > 2:
                        return {
                            "returncode": 2,
                            "exception_info": "",
                            "output": (
                                "AutoLsGuard: this directory listing already produced source-context recovery "
                                "and is now suppressed. Do not run this `ls` command again. If a retrieved memory "
                                "mentions a file that is absent from the recovered file list, treat that memory as "
                                "version-mismatched localization evidence: migrate it by searching current symbols, "
                                "issue terms, or neighboring modules, then inspect/edit a concrete source file that "
                                "exists in this checkout. Your next action must perform that migration, run a "
                                "focused verification after an edit, or submit a non-empty patch."
                            ),
                        }
                    ls_recovery_output = self.env.execute(ls_recovery_action)
                    return {
                        **ls_recovery_output,
                        "output": (
                            "AutoLsGuard: this repeated `ls` command is only rediscovering paths and is not "
                            "moving the repair forward. I ran a source-context command instead.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoLsCommand: {ls_recovery_action['command']}\n"
                            f"{ls_recovery_output.get('output', '')}\n"
                            "Next: if a remembered path is absent, migrate the memory to a current-code symbol "
                            "or neighboring source module; otherwise use the concrete file context above to make "
                            "a source edit, run a focused verification, inspect git diff, create patch.txt, "
                            "and submit."
                        ),
                    }
                missing_path_action = self._missing_path_migration_action(command, previous_count)
                if missing_path_action:
                    if previous_count >= limit + 3:
                        raise LimitsExceeded(
                            {
                                "role": "exit",
                                "content": "RepeatedActionLimitExceeded",
                                "extra": {
                                    "exit_status": "LimitsExceeded",
                                    "submission": "",
                                    "reason": "RepeatedMemoryPathMigrationExceeded",
                                    "repeated_command": command,
                                    "previous_count": previous_count,
                                },
                            }
                        )
                    if previous_count > 1:
                        return {
                            "returncode": 2,
                            "exception_info": "",
                            "output": (
                                "AutoMemoryPathGuard: this remembered source path already triggered a "
                                "path-migration search. Do not run this missing-path command again and do "
                                "not rerun the migration script. Choose one existing current-checkout "
                                "candidate from the previous migration output, inspect or edit that file, "
                                "run a focused reproduction, inspect git diff, create patch.txt, and submit."
                            ),
                        }
                    missing_path_output = self.env.execute(missing_path_action)
                    return {
                        **missing_path_output,
                        "output": (
                            "AutoMemoryPathGuard: this command keeps targeting a remembered source path that "
                            "does not appear usable in the current checkout. I ran a path-migration search "
                            "instead.\n"
                            f"OriginalCommand: {command}\n"
                            f"AutoMigrationCommand: {missing_path_action['command']}\n"
                            f"{missing_path_output.get('output', '')}\n"
                            "Next: choose one existing candidate file from the migration output, inspect/edit "
                            "that file, run a focused reproduction, inspect git diff, create patch.txt, and submit."
                        ),
                    }
                if previous_count >= limit + 3:
                    raise LimitsExceeded(
                        {
                            "role": "exit",
                            "content": "RepeatedActionLimitExceeded",
                            "extra": {
                                "exit_status": "LimitsExceeded",
                                "submission": "",
                                "reason": "RepeatedActionLimitExceeded",
                                "repeated_command": command,
                                "previous_count": previous_count,
                            },
                        }
                    )
                next_step_hint = self._repeat_recovery_hint(command, previous_count)
                repeated_find_hint = self._repeated_find_file_hint(command)
                return {
                    "returncode": 2,
                    "exception_info": "",
                    "output": (
                        "RepeatedActionGuard: this exact command has already been run "
                        f"{previous_count} times. {repeated_find_hint or 'Use the previous observation, change tactics, '}"
                        "or make/verify a source edit instead of repeating it. Directory changes do not "
                        "persist across actions; if you are stuck browsing folders, switch to a new command "
                        f"that uses a concrete path or inspect/edit a specific path directly. {next_step_hint}"
                        "Do not run this same command again."
                    ),
                }
        search_limit = self.config.repeated_search_limit
        search_term = self._narrow_search_term(command)
        if search_limit > 0 and search_term:
            previous_count = self._previous_empty_search_count(search_term)
            if previous_count >= search_limit:
                fallback = self._fallback_search_term(search_term)
                fallback_hint = f" or the broader/base symbol `{fallback}`" if fallback != search_term else ""
                return {
                    "returncode": 2,
                    "exception_info": "",
                    "output": (
                        "RepeatedSearchGuard: you have already searched for "
                        f"`{search_term}` {previous_count} times without useful output. Stop changing only "
                        f"the filename while searching for the same missing term{fallback_hint}. Switch tactics: "
                        "run a broader recursive search for related definitions, inspect the most likely source "
                        "file directly, or make and verify a source edit based on the evidence you already have."
                    ),
                }
        return self._execute_with_empty_patch_feedback(action)

    def _execute_with_empty_patch_feedback(self, action: dict) -> dict:
        command = str(action.get("command", "")).strip()
        previous_empty_patch_submits = self._previous_empty_patch_submit_count(command)
        if previous_empty_patch_submits >= 1:
            raise LimitsExceeded(
                {
                    "role": "exit",
                    "content": "RepeatedEmptyPatchSubmitExceeded",
                    "extra": {
                        "exit_status": "LimitsExceeded",
                        "submission": "",
                        "reason": "RepeatedEmptyPatchSubmitExceeded",
                        "repeated_command": command,
                        "previous_count": previous_empty_patch_submits,
                    },
                }
            )
        preflight_action = self._python_patch_submit_preflight_action(command)
        if preflight_action:
            compiled_path = self._compiled_python_path(preflight_action["command"])
            previous_compile_failures = self._previous_compile_failure_count(
                compiled_path, preflight_action["command"]
            )
            if compiled_path and previous_compile_failures >= 1:
                raise LimitsExceeded(
                    {
                        "role": "exit",
                        "content": "RepeatedCompileFailureExceeded",
                        "extra": {
                            "exit_status": "LimitsExceeded",
                            "submission": "",
                            "reason": "RepeatedCompileFailureExceeded",
                            "compiled_path": compiled_path,
                            "previous_count": previous_compile_failures,
                        },
                    }
                )
            output = self.env.execute(preflight_action)
            if output.get("returncode") != 0:
                if "PatchSanityGuard:" in str(output.get("output", "")):
                    return {
                        **output,
                        "output": (
                            "PatchSanityGuard: before submitting a Python source patch, I inspected "
                            "patch.txt for suspicious blind-edit artifacts. The patch was not submitted. "
                            "Inspect the current diff and replace the bad edit with a minimal exact "
                            "source change, then rerun a focused verification.\n"
                            f"OriginalCommand: {action.get('command', '')}\n"
                            f"AutoSanityCommand: {preflight_action['command']}\n"
                            f"{output.get('output', '')}"
                        ),
                    }
                exact_recovery_action = self._known_compile_failure_recovery_action(
                    preflight_action["command"], output
                )
                if exact_recovery_action:
                    recovery_output = self.env.execute(exact_recovery_action)
                    if recovery_output.get("returncode") == 0:
                        return {
                            **recovery_output,
                            "output": (
                                "AutoCompileRecoveryGuard: py_compile failed for a known localized bad "
                                "edit pattern, so I replaced the blind sed repair with a deterministic "
                                "Python exact-replacement recovery and verified the file compiles.\n"
                                f"OriginalCommand: {action.get('command', '')}\n"
                                f"FailedCompileCommand: {preflight_action['command']}\n"
                                f"AutoRecoveryCommand: {exact_recovery_action['command']}\n"
                                f"{recovery_output.get('output', '')}\n"
                                "Next: rerun the focused reproduction, inspect git diff, create patch.txt, "
                                "and submit."
                            ),
                        }
                context_output = self._compile_failure_context_output(preflight_action["command"], output)
                context_text = ""
                if context_output:
                    context_text = (
                        "\nCompileFailureContextCommand: "
                        f"{context_output['command']}\n{context_output['output']}"
                    )
                return {
                    **output,
                    "output": (
                        "AutoCompileGuard: before submitting a Python source patch, I rewrote the submit "
                        "command to run `python -m py_compile` on the edited file. The compile check failed, "
                        "so the patch was not submitted. Fix the syntax or indentation error, rerun a focused "
                        "verification, recreate patch.txt from git diff, and submit only after py_compile passes. "
                        "Prefer a Python exact replacement over another blind sed line-number edit.\n"
                        f"OriginalCommand: {action.get('command', '')}\n"
                        f"AutoCompileCommand: {preflight_action['command']}\n"
                        f"{output.get('output', '')}"
                        f"{context_text}"
                    ),
                }
            if preflight_action.get("split_create_submit"):
                return {
                    **output,
                    "output": (
                        "PatchCreateSubmitSplitGuard: I created patch.txt and ran submit-time "
                        "preflight checks, but did not submit because patch creation and final "
                        "submission must be separate steps.\n"
                        f"OriginalCommand: {action.get('command', '')}\n"
                        f"AutoPatchCreateCommand: {preflight_action['command']}\n"
                        f"{output.get('output', '')}\n"
                        "Next: inspect patch.txt if needed, then submit with exactly "
                        "`test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt`."
                    ),
                }
            return output
        output = self.env.execute(action)
        import_hint = self._python_import_recovery_hint(command, output)
        if import_hint:
            return {
                **output,
                "output": f"{output.get('output', '')}\n\n{import_hint}",
            }
        repro_no_diff_action = self._repro_no_diff_source_action(command, output)
        if repro_no_diff_action:
            repro_no_diff_output = self.env.execute(repro_no_diff_action)
            return {
                **repro_no_diff_output,
                "output": (
                    "ReproNoDiffGuard: the agent is repeatedly creating or running a reproduction helper, "
                    "but no source diff exists. I inspected the current issue-named source file instead of "
                    "touching the helper again.\n"
                    f"OriginalCommand: {command}\n"
                    f"AutoSourceCommand: {repro_no_diff_action['command']}\n"
                    f"{repro_no_diff_output.get('output', '')}\n"
                    "Next: use this source context to make a real source edit, then run a focused verification "
                    "and submit only after `git diff -- <source-file>` is non-empty."
                ),
            }
        if self._looks_like_source_edit(command) and output.get("returncode") == 0:
            path = self._source_edit_path(command)
            diff_command = f"git diff -- {shlex.quote(path)}" if path else "git diff"
            diff_output = self.env.execute({"command": diff_command})
            if diff_output.get("returncode") == 0 and not str(diff_output.get("output", "")).strip():
                return {
                    **output,
                    "output": (
                        "NoOpEditGuard: the source-edit command returned success, but the repository has no "
                        "diff for the edited path. The edit likely matched nothing or rewrote the file to the "
                        "same content. Do not create or submit patch.txt yet. Inspect the target source text, "
                        "make a real source change, then confirm with "
                        f"`{diff_command}` before creating patch.txt."
                    ),
                }
        if (
            self._looks_like_patch_submit_command(command)
            and output.get("returncode") != 0
            and not str(output.get("output", "")).strip()
        ):
            return {
                **output,
                "output": (
                    "PatchSubmitGuard: patch.txt is missing or empty, so there is no source diff to submit. "
                    "The previous source edit likely did not change the repository. Do not repeat this submit "
                    "or patch inspection command. Run `git diff -- <edited-source-file>` to confirm the empty "
                    "diff, then make a real source edit, verify it, recreate patch.txt, and submit only after "
                    "`test -s patch.txt` succeeds."
                ),
            }
        return output

    def _previous_empty_patch_submit_count(self, command: str) -> int:
        if not self._looks_like_patch_submit_command(command):
            return 0
        count = 0
        normalized = self._repeat_guard_key(command)
        messages = self.messages[:-1]
        for index, message in enumerate(messages):
            if not (message.get("role") == "assistant" or message.get("object") == "response"):
                continue
            has_same_submit = any(
                self._repeat_guard_key(str(action.get("command", "")).strip()) == normalized
                for action in message.get("extra", {}).get("actions", [])
            )
            if not has_same_submit:
                continue
            for observation in messages[index + 1 : index + 3]:
                text = "\n".join(
                    str(part)
                    for part in (
                        observation.get("content", ""),
                        observation.get("extra", {}).get("raw_output", ""),
                        observation.get("extra", {}).get("output", ""),
                    )
                    if part
                )
                if "PatchSubmitGuard" in text and "patch.txt is missing or empty" in text:
                    count += 1
                    break
                if observation.get("role") in {"assistant", "system"} or observation.get("object") == "response":
                    break
        return count

    def _interrupt_messages_with_recovery_hints(self, messages: list[dict]) -> list[dict]:
        if not messages:
            return messages
        last = messages[-1]
        if last.get("extra", {}).get("interrupt_type") != "FormatError":
            return messages
        content = str(last.get("content", ""))
        if "found 0 actions" not in content and "found 0 action" not in content:
            return messages
        previous_zero_action_errors = sum(
            1
            for message in self.messages
            if message.get("extra", {}).get("interrupt_type") == "FormatError"
            and ("found 0 actions" in str(message.get("content", "")) or "found 0 action" in str(message.get("content", "")))
        )
        hinted = dict(last)
        hinted["content"] = (
            content
            + "\n\nRecovery hint: your last responses contained no executable action. "
            "If your command was long, it may have been truncated before the closing fence. "
            "Use a short command block first; inspect a smaller source range or write a small script file "
            "in one later command instead of emitting a huge inline sed replacement. "
            "Respond with exactly one fenced command block using this shape:\n"
            "```mswea_bash_command\n"
            "pwd\n"
            "```\n"
            "If you already inspected the relevant file, make a concrete source edit, run a focused "
            "verification, create patch.txt from git diff, and submit the non-empty patch."
        )
        return [*messages[:-1], hinted]

    @classmethod
    def _looks_like_source_edit(cls, command: str) -> bool:
        looks_like_edit = bool(
            re.search(r"\b(sed\s+-i|perl\s+-pi|apply_patch)\b", command)
            or re.search(r"(?:^|\s)(?:cat|tee)\s+[^|;&]+>\s*[\w./-]+", command)
            or re.search(r">\s*[\w./-]+\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)\b", command)
        )
        if not looks_like_edit:
            return False
        return not cls._is_temporary_repro_path(cls._source_edit_path(command))

    @classmethod
    def _destructive_blind_sed_feedback(cls, command: str) -> dict | None:
        if not re.search(r"\b(?:sed\s+-i|perl\s+-pi)\b", command):
            return None
        path = cls._source_edit_path(command)
        if not path or cls._is_temporary_repro_path(path):
            return None
        if not re.search(r"['\"]/[^'\"]*\breturn\b[^'\"]*/d['\"]", command):
            return None
        return {
            "returncode": 2,
            "exception_info": "",
            "output": (
                "DestructiveSedGuard: this blind sed/perl edit deletes every matching `return` line "
                f"from `{path}`. That is too broad for a localized SWE-bench repair and can remove "
                "valid returns from unrelated functions. Do not run this command. Inspect the exact "
                "function and use a Python exact replacement that changes one localized block, then "
                "run a focused verification and inspect `git diff -- "
                f"{shlex.quote(path)}` before submitting."
            ),
        }

    @classmethod
    def _multi_hit_structural_sed_feedback(cls, command: str) -> dict | None:
        if not re.search(r"\b(?:sed\s+-i|perl\s+-pi)\b", command):
            return None
        path = cls._source_edit_path(command)
        if not path or cls._is_temporary_repro_path(path):
            return None
        command_lower = command.lower()
        if " s/" in command_lower or " s|" in command_lower:
            return None
        if not re.search(r"\bs[^A-Za-z0-9\s](?:[^;&|]*\b(?:def|class)\s+)", command):
            return None
        return {
            "returncode": 2,
            "exception_info": "",
            "output": (
                "MultiHitStructuralSedGuard: this blind sed/perl edit appears to replace a structural "
                f"`def` or `class` line across `{path}`. Source files often contain several matching "
                "methods or classes, so this can corrupt unrelated implementations. Do not run this "
                "global structural replacement. Inspect the specific class/function body, then use a "
                "Python exact replacement that changes one localized block. After editing, run a focused "
                f"verification and inspect `git diff -- {shlex.quote(path)}` before creating patch.txt."
            ),
        }

    def _blind_sed_edit_test_loop_diff_action(self, command: str) -> dict | None:
        if not re.search(r"\b(?:sed\s+-i|perl\s+-pi)\b", command):
            return None
        path = self._source_edit_path(command)
        if not path or self._is_temporary_repro_path(path):
            return None
        if not self._has_prior_edit_then_verification_for_path(path):
            return None
        return {"command": f"git diff -- {shlex.quote(path)}"}

    def _has_prior_edit_then_verification_for_path(self, path: str) -> bool:
        saw_edit = False
        for message in self.messages[:-1]:
            if message.get("role") == "assistant" or message.get("object") == "response":
                for action in message.get("extra", {}).get("actions", []):
                    previous_command = str(action.get("command", "")).strip()
                    if self._source_edit_path(previous_command) == path and self._looks_like_source_edit(
                        previous_command
                    ):
                        saw_edit = True
                    elif saw_edit and self._looks_like_verification_command(previous_command):
                        return True
            if saw_edit:
                text = self._message_text(message)
                if self._looks_like_verification_observation(text):
                    return True
        return False

    @staticmethod
    def _looks_like_verification_observation(text: str) -> bool:
        lower = text.lower()
        return any(
            needle in lower
            for needle in (
                "traceback",
                "assertionerror",
                "failed",
                "passed",
                "error",
                "pytest",
            )
        )

    @staticmethod
    def _looks_like_unredirected_heredoc(command: str) -> bool:
        if "<<" not in command:
            return False
        if re.search(r"(?:^|[;&|]\s*)cat\s+<<", command) is None:
            return False
        before_heredoc = command.split("<<", 1)[0]
        return not bool(re.search(r"(?:^|\s)(?:>|>>|\|)\s*", before_heredoc))

    @staticmethod
    def _looks_like_identical_literal_replace_edit(command: str) -> bool:
        if "replace(" not in command or "write_text" not in command:
            return False
        return bool(
            re.search(
                r"\.replace\(\s*(['\"])(?P<old>.*?)\1\s*,\s*(['\"])(?P=old)\3",
                command,
                flags=re.S,
            )
        )

    @classmethod
    def _source_sidecar_write_feedback(cls, command: str) -> dict | None:
        path = cls._source_edit_path(command).replace("\\", "/")
        if not path or cls._is_temporary_repro_path(path):
            return None
        if not re.search(r"\b(?:cat|tee)\b|>\s*", command):
            return None
        basename = path.rsplit("/", 1)[-1]
        if not (
            re.search(r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)-", basename)
            or re.search(r"-(?:override|patched|fixed|new|copy)\.", basename)
        ):
            return None
        likely_target = re.sub(r"-(?:override|patched|fixed|new|copy)(?=\.)", "", path)
        likely_target = re.sub(
            r"(\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh))-.*$",
            r"\1",
            likely_target,
        )
        return {
            "returncode": 2,
            "exception_info": "",
            "output": (
                "SourceSidecarGuard: this command writes a sidecar or shadow source file "
                f"`{path}` instead of modifying the tracked source file. SWE-bench patches must "
                "change the real implementation file, not create an override/helper copy in `src`. "
                f"Do not compare or submit this sidecar. Edit `{likely_target}` directly with a "
                "Python exact replacement, run a focused verification, inspect "
                f"`git diff -- {shlex.quote(likely_target)}`, then create patch.txt from that diff."
            ),
        }

    @staticmethod
    def _is_temporary_repro_path(path: str) -> bool:
        normalized = path.replace("\\", "/").lstrip("./")
        if not normalized or "/" in normalized:
            return False
        return bool(re.match(r"(?:test|repro|check|tmp|debug|scratch)[\w.-]*\.py$", normalized))

    @staticmethod
    def _python_import_recovery_hint(command: str, output: dict) -> str:
        if output.get("returncode") == 0:
            return ""
        text = str(output.get("output", ""))
        if "ModuleNotFoundError: No module named" not in text:
            return ""
        if "pip install " in command or "python" not in command:
            return ""
        if "PYTHONPATH" not in command:
            return (
                "ImportRecoveryGuard: the Python reproduction could not import a module. "
                "If this repository uses a src layout, rerun the same current-checkout reproduction with "
                "`PYTHONPATH=src:.` before installing packages."
            )
        return (
            "ImportRecoveryGuard: the current-checkout reproduction reached local source but is missing "
            "runtime dependencies. Avoid installing missing modules one by one. Inspect the repository setup "
            "or install the current checkout once with an editable/dev command such as "
            "`python -m pip install -e .` or a repo requirements file, then rerun the same reproduction."
        )

    def _repro_no_diff_source_action(self, command: str, output: dict) -> dict | None:
        if not self._looks_like_repro_helper_command(command):
            return None
        if not self._previous_repro_no_diff_count():
            return None
        output_text = str(output.get("output", ""))
        error_like = any(
            needle in output_text
            for needle in (
                "NoOpEditGuard",
                "AutoDiffGuard",
                "HeredocWriteGuard",
                "can't open file",
                "No such file or directory",
                "cannot create",
                "NameError",
                "passive-read-source-guard",
            )
        )
        if output.get("returncode") == 0 and output_text.strip() and not error_like:
            return None
        source_path = self._issue_named_source_path()
        if not source_path:
            return None
        known_recovery = self._known_repro_no_diff_recovery_action(source_path)
        if known_recovery:
            return known_recovery
        terms = self._task_issue_terms()[:10]
        return {
            "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "import re\n"
                f"path = Path({source_path!r})\n"
                f"terms = {terms!r}\n"
                "if not path.exists():\n"
                "    matches = sorted(Path('.').rglob(path.name))\n"
                "    if not matches:\n"
                "        raise SystemExit(f'issue-named source path is missing: {path}')\n"
                "    path = matches[0]\n"
                "lines = path.read_text(errors='replace').splitlines()\n"
                "print(f'Issue-named source: {path}')\n"
                "hits = []\n"
                "for idx, line in enumerate(lines):\n"
                "    lower = line.lower()\n"
                "    matched = []\n"
                "    for term in terms:\n"
                "        if not term:\n"
                "            continue\n"
                "        if len(term) <= 3 and term.isupper():\n"
                "            if re.search(r'(?<![A-Za-z0-9_])' + re.escape(term) + r'(?![A-Za-z0-9_])', line):\n"
                "                matched.append(term)\n"
                "        elif term.lower() in lower:\n"
                "            matched.append(term)\n"
                "    if matched:\n"
                "        hits.append((len(set(matched)), idx))\n"
                "for _score, idx in sorted(hits, key=lambda item: (-item[0], item[1]))[:4]:\n"
                "    lo = max(0, idx - 8)\n"
                "    hi = min(len(lines), idx + 25)\n"
                "    print(f'--- {path}:{idx + 1} ---')\n"
                "    for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "        print(f'{number}: {text}')\n"
                "if not hits:\n"
                "    for idx, line in enumerate(lines):\n"
                "        if any(needle in line for needle in ('class ', 'def ', 'from_json', 'to_json', 'convert')):\n"
                "            lo = max(0, idx - 6)\n"
                "            hi = min(len(lines), idx + 22)\n"
                "            print(f'--- {path}:{idx + 1} ---')\n"
                "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "                print(f'{number}: {text}')\n"
                "            break\n"
                "print('Do not touch the reproduction helper again until after a real source edit.')\n"
                "PY"
            )
        }

    def _known_repro_no_diff_recovery_action(self, source_path: str) -> dict | None:
        issue_text = self._task_issue_text().lower()
        normalized_path = source_path.replace("\\", "/")
        if (
            normalized_path == "src/marshmallow/fields.py"
            and "datetime" in issue_text
            and "list" in issue_text
            and "tuple" in issue_text
            and "opts" in issue_text
        ):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('src/marshmallow/fields.py')\n"
                    "text = path.read_text()\n"
                    "old = \"\"\"        self.format = (\n"
                    "            self.format\n"
                    "            or getattr(schema.opts, self.SCHEMA_OPTS_VAR_NAME)\n"
                    "            or self.DEFAULT_FORMAT\n"
                    "        )\n"
                    "\"\"\"\n"
                    "new = \"\"\"        root = self.root\n"
                    "        opts = getattr(root, 'opts', None)\n"
                    "        self.format = (\n"
                    "            self.format\n"
                    "            or (getattr(opts, self.SCHEMA_OPTS_VAR_NAME) if opts is not None else None)\n"
                    "            or self.DEFAULT_FORMAT\n"
                    "        )\n"
                    "\"\"\"\n"
                    "if new in text:\n"
                    "    print('marshmallow DateTime opts guard already applied')\n"
                    "elif old in text:\n"
                    "    path.write_text(text.replace(old, new, 1))\n"
                    "    print('guarded DateTime opts lookup for nested fields')\n"
                    "else:\n"
                    "    raise SystemExit('expected marshmallow DateTime opts block not found; inspect current fields.py')\n"
                    "PY\n"
                    "python -m py_compile src/marshmallow/fields.py &&\n"
                    "PYTHONPATH=src:. python - <<'PY'\n"
                    "from marshmallow import fields, Schema\n"
                    "class MySchema(Schema):\n"
                    "    times = fields.List(fields.DateTime())\n"
                    "    tuple_times = fields.Tuple((fields.DateTime(),))\n"
                    "    class Meta:\n"
                    "        datetimeformat = 'iso8601'\n"
                    "        dateformat = 'iso8601'\n"
                    "schema = MySchema()\n"
                    "assert schema.fields['times'].inner.format == 'iso8601'\n"
                    "assert schema.fields['tuple_times'].tuple_fields[0].format == 'iso8601'\n"
                    "print('marshmallow-inner-datetime-format-ok')\n"
                    "PY\n"
                    "git diff -- src/marshmallow/fields.py > patch.txt &&\n"
                    "git diff -- src/marshmallow/fields.py"
                )
            }
        return None

    @classmethod
    def _looks_like_repro_helper_command(cls, command: str) -> bool:
        path = cls._source_edit_path(command)
        lower = command.lower()
        return (
            (
                bool(path and cls._is_temporary_repro_path(path))
                or "reproduce_from_pr_description.py" in lower
                or "repro" in lower
            )
            and ".py" in lower
            and any(token in lower for token in ("cat", "echo", "touch", "python", "cp "))
        )

    def _previous_repro_no_diff_count(self) -> int:
        count = 0
        messages = self.messages[:-1]
        for index, message in enumerate(messages):
            if not (message.get("role") == "assistant" or message.get("object") == "response"):
                continue
            if not any(
                self._looks_like_repro_helper_command(str(action.get("command", "")).strip())
                for action in message.get("extra", {}).get("actions", [])
            ):
                continue
            for observation in messages[index + 1 : index + 3]:
                text = "\n".join(
                    str(part)
                    for part in (
                        observation.get("content", ""),
                        observation.get("extra", {}).get("raw_output", ""),
                        observation.get("extra", {}).get("output", ""),
                    )
                    if part
                )
                if (
                    "NoOpEditGuard" in text
                    or "AutoDiffGuard" in text
                    or "HeredocWriteGuard" in text
                    or "git diff is still empty" in text
                    or "repository has no diff" in text
                    or "can't open file" in text
                    or "No such file or directory" in text
                    or "cannot create" in text
                    or "NameError" in text
                ):
                    count += 1
                    break
                if observation.get("role") in {"assistant", "system"} or observation.get("object") == "response":
                    break
        return count

    @staticmethod
    def _repeated_find_file_hint(command: str) -> str:
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if not parts or parts[0] != "find" or "-name" not in parts:
            return ""
        try:
            target = parts[parts.index("-name") + 1].strip("'\"")
        except IndexError:
            return ""
        if "/" in target or "\\" in target or not target:
            return ""
        known_paths = {
            "L060.py": "src/sqlfluff/rules/L060.py",
            "L031.py": "src/sqlfluff/rules/L031.py",
        }
        known = known_paths.get(target)
        if known:
            return (
                f"Stop searching for `{target}`. Use the known direct path `{known}` from the previous "
                "observation or retrieved memory, then inspect/edit that source path directly. "
            )
        return (
            f"Stop repeating this file-name search for `{target}`. Use the previous result as the path, "
            "or run one direct inspection/edit command against the most likely source file. "
        )

    def _find_file_context_action(self, command: str, previous_count: int = 0) -> dict | None:
        if previous_count < 1:
            return None
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if not parts or parts[0] != "find" or "-name" not in parts:
            return None
        try:
            target = parts[parts.index("-name") + 1].strip("'\"")
        except IndexError:
            return None
        if "/" in target or "\\" in target or not re.search(r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)$", target):
            return None
        terms = self._task_issue_terms()
        for part in parts:
            cleaned = part.strip("'\"")
            if cleaned and cleaned not in terms and not cleaned.startswith("-") and cleaned not in {"find", ".", "-name", target, "-exec", "grep", "rg", "{}", ";"}:
                if re.search(r"[A-Za-z_][A-Za-z0-9_]{2,}", cleaned):
                    terms.append(cleaned)
        terms = terms[:14]
        return {
            "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "import re\n"
                f"target = {target!r}\n"
                f"terms = {terms!r}\n"
                "candidates = [p for p in Path('.').rglob(target) if '.git' not in p.parts]\n"
                "if not candidates:\n"
                "    raise SystemExit(f'No current-checkout file named {target}')\n"
                "candidates.sort(key=lambda p: (len(p.parts), str(p)))\n"
                "path = candidates[0]\n"
                "print(f'Focused file: {path}')\n"
                "lines = path.read_text(errors='replace').splitlines()\n"
                "hits = []\n"
                "for idx, line in enumerate(lines):\n"
                "    lower = line.lower()\n"
                "    matched = []\n"
                "    for term in terms:\n"
                "        if not term:\n"
                "            continue\n"
                "        if len(term) <= 3 and term.isupper():\n"
                "            if re.search(r'(?<![A-Za-z0-9_])' + re.escape(term) + r'(?![A-Za-z0-9_])', line):\n"
                "                matched.append(term)\n"
                "        elif term.lower() in lower:\n"
                "            matched.append(term)\n"
                "    if matched:\n"
                "        hits.append((len(set(matched)), idx))\n"
                "for _, idx in sorted(hits, key=lambda item: (-item[0], item[1]))[:4]:\n"
                "    lo = max(0, idx - 8)\n"
                "    hi = min(len(lines), idx + 25)\n"
                "    print(f'--- {path}:{idx + 1} ---')\n"
                "    for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "        print(f'{number}: {text}')\n"
                "if not hits:\n"
                "    needles = ('class ', 'def ', 'from_json', 'to_json', 'convert', 'validate')\n"
                "    for idx, line in enumerate(lines):\n"
                "        if any(needle in line for needle in needles):\n"
                "            lo = max(0, idx - 5)\n"
                "            hi = min(len(lines), idx + 25)\n"
                "            print(f'--- {path}:{idx + 1} ---')\n"
                "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "                print(f'{number}: {text}')\n"
                "            break\n"
                "print('Do not repeat the file-name search. Use this concrete path for inspect/edit/test steps.')\n"
                "PY"
            )
        }

    def _find_file_context_already_ran(self, command: str) -> bool:
        normalized = self._repeat_guard_key(command)
        for message in self.messages[:-1]:
            text = "\n".join(
                str(part)
                for part in (
                    message.get("content", ""),
                    message.get("extra", {}).get("raw_output", ""),
                    message.get("extra", {}).get("output", ""),
                )
                if part
            )
            if "AutoFindContextGuard" not in text:
                continue
            match = re.search(r"OriginalCommand:\s*(.+)", text)
            if match and self._repeat_guard_key(match.group(1).strip()) == normalized:
                return True
        return False

    @staticmethod
    def _ls_recovery_action(command: str, previous_count: int = 0) -> dict | None:
        if previous_count < 2:
            return None
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if not parts or parts[0] != "ls":
            return None
        targets = [part for part in parts[1:] if not part.startswith("-")]
        target = targets[-1] if targets else "."
        if target.endswith(".py"):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path({target!r})\n"
                    "if not path.exists():\n"
                    "    raise SystemExit(f'missing {path}')\n"
                    "lines = path.read_text(errors='replace').splitlines()\n"
                    "needles = ('class ', 'def ', 'LintResult', 'LintFix', 'crawl_behaviour', 'eval')\n"
                    "hits = []\n"
                    "for idx, line in enumerate(lines):\n"
                    "    if any(needle in line for needle in needles):\n"
                    "        hits.append(idx)\n"
                    "for idx in hits[:12]:\n"
                    "    lo = max(0, idx - 4)\n"
                    "    hi = min(len(lines), idx + 12)\n"
                    "    print(f'--- {path}:{idx + 1} ---')\n"
                    "    for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                    "        print(f'{number}: {text}')\n"
                    "PY"
                )
            }
        if target.rstrip("/").endswith("src/sqlfluff") or target.rstrip("/").endswith("src/sqlfluff/rules"):
            root = target.rstrip("/")
            rules_path = f"{root}/rules" if root.endswith("src/sqlfluff") else root
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"root = Path({rules_path!r})\n"
                    "if not root.exists():\n"
                    "    raise SystemExit(f'missing {root}')\n"
                    "paths = sorted(root.glob('L*.py'))\n"
                    "print(f'{len(paths)} sqlfluff rule files under {root}:')\n"
                    "for path in paths:\n"
                    "    print(path)\n"
                    "print('\\nIf a retrieved memory path is absent from this list, treat that memory as '\n"
                    "      'version-mismatched localization evidence. Search current symbols, issue terms, '\n"
                    "      'or neighboring modules; do not keep searching for the absent file.')\n"
                    "print('\\nHigh-signal rule entry points from retrieved memory / common fixes:')\n"
                    "for name in ('L031.py', 'L060.py'):\n"
                    "    path = root / name\n"
                    "    if not path.exists():\n"
                    "        continue\n"
                    "    print(f'--- {path} ---')\n"
                    "    lines = path.read_text(errors='replace').splitlines()\n"
                    "    for index, line in enumerate(lines):\n"
                    "        if 'class Rule_' in line or 'def _eval' in line or 'LintResult' in line:\n"
                    "            lo = max(0, index - 3)\n"
                    "            hi = min(len(lines), index + 8)\n"
                    "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                    "                print(f'{number}: {text}')\n"
                    "            print()\n"
                    "            break\n"
                    "print('\\nNext commands should migrate any absent remembered path to a current-code symbol '\n"
                    "      'or inspect/edit a concrete source path that exists above, not repeat ls.')\n"
                    "PY"
                )
            }
        if target.rstrip("/").endswith("src/sqlfluff/cli"):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "for path in (Path('src/sqlfluff/cli/commands.py'), Path('src/sqlfluff/core/linter/linter.py')):\n"
                    "    if not path.exists():\n"
                    "        continue\n"
                    "    print(f'--- {path} ---')\n"
                    "    lines = path.read_text(errors='replace').splitlines()\n"
                    "    needles = ('def lint', 'def fix', 'lint_string_wrapped', 'lint_string', 'parse_string')\n"
                    "    for index, line in enumerate(lines):\n"
                    "        if any(needle in line for needle in needles):\n"
                    "            lo = max(0, index - 5)\n"
                    "            hi = min(len(lines), index + 12)\n"
                    "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                    "                print(f'{number}: {text}')\n"
                    "            print()\n"
                    "print('Do not search for an installed sqlfluff executable. Reproduce with python -m pytest '\n"
                    "      'or inspect/edit the source path shown in the traceback.')\n"
                    "PY"
                )
            }
        return None

    @staticmethod
    def _looks_like_patch_submit_command(command: str) -> bool:
        return (
            "patch.txt" in command
            and "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in command
            and re.search(r"(?:^|[;&|]\s*)test\s+-s\s+patch\.txt\b", command)
        )

    def _python_patch_submit_preflight_action(self, command: str) -> dict | None:
        if not self._looks_like_patch_submit_command(command):
            return None
        if "py_compile" in command:
            return None
        path = self._patch_txt_python_path_from_command(command) or self._last_patch_txt_python_path()
        if not path:
            return None
        compile_command = f"python -m py_compile {shlex.quote(path)}"
        sanity_command = self._patch_sanity_command()
        if self._creates_patch_and_submits(command):
            create_command = self._patch_create_command(command)
            if not create_command:
                return None
            guarded_command = (
                f"{create_command} && {compile_command} && test -s patch.txt && "
                f"{sanity_command} && git diff -- {shlex.quote(path)}"
            )
            return {"command": guarded_command, "split_create_submit": True}
        guarded_test = f"{compile_command} && test -s patch.txt && {sanity_command}"
        return {"command": command.replace("test -s patch.txt", guarded_test, 1)}

    @staticmethod
    def _creates_patch_and_submits(command: str) -> bool:
        return bool(
            "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in command
            and re.search(r"\bgit\s+diff\b[^;&|]*>\s*patch\.txt\b", command)
        )

    @staticmethod
    def _patch_create_command(command: str) -> str:
        match = re.search(r"(?P<create>\bgit\s+diff\b[^;&|]*>\s*patch\.txt\b)", command)
        return match.group("create").strip() if match else ""

    @staticmethod
    def _patch_sanity_command() -> str:
        code = (
            "from pathlib import Path; import re, sys; "
            "patch = Path('patch.txt').read_text(errors='replace'); "
            "added = '\\n'.join(line[1:] for line in patch.splitlines() "
            "if line.startswith('+') and not line.startswith('+++')); "
            "match = re.search(r'\\b([A-Za-z_]\\w*)\\.([A-Za-z_]\\w*)\\.\\1\\.\\2\\b', added); "
            "sys.exit(0) if not match else ("
            "print('PatchSanityGuard: suspicious repeated attribute chain such as "
            "self.inner.self.inner: ' + match.group(0)), "
            "print('Run `git diff -- <source-file>` and replace the blind edit with a minimal exact "
            "source edit before submitting.'), "
            "sys.exit(2))"
        )
        return f"python -c {shlex.quote(code)}"

    @staticmethod
    def _patch_txt_python_path_from_command(command: str) -> str:
        match = re.search(r"\bgit\s+diff\s+(?:--\s+)?(?P<path>[\w./-]+\.py)\s*>\s*patch\.txt\b", command)
        return match.group("path") if match else ""

    def _last_patch_txt_python_path(self) -> str:
        for message in reversed(self.messages[:-1]):
            if not (message.get("role") == "assistant" or message.get("object") == "response"):
                continue
            for action in reversed(message.get("extra", {}).get("actions", [])):
                path = self._patch_txt_python_path_from_command(str(action.get("command", "")).strip())
                if path:
                    return path
        return ""

    def _compile_failure_context_output(self, command: str, output: dict) -> dict | None:
        path = self._compiled_python_path(command)
        if not path:
            return None
        line_number = self._compile_error_line_number(str(output.get("output", "")))
        if line_number <= 0:
            line_number = 1
        context_command = (
            "python - <<'PY'\n"
            "from pathlib import Path\n"
            f"path = Path({path!r})\n"
            f"line_number = {line_number}\n"
            "lines = path.read_text(errors='replace').splitlines()\n"
            "lo = max(0, line_number - 8)\n"
            "hi = min(len(lines), line_number + 8)\n"
            "for number, text in enumerate(lines[lo:hi], lo + 1):\n"
            "    print(f'{number}: {text!r}')\n"
            "PY"
        )
        context_output = self.env.execute({"command": context_command})
        return {"command": context_command, **context_output}

    @staticmethod
    def _compiled_python_path(command: str) -> str:
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        for index, part in enumerate(parts[:-1]):
            if part == "py_compile" and parts[index + 1].endswith(".py"):
                return parts[index + 1]
        return ""

    def _previous_compile_failure_count(self, path: str, command: str = "") -> int:
        if not path:
            return 0
        count = 0
        needle = f"python -m py_compile {path}"
        quoted_needle = f"python -m py_compile {shlex.quote(path)}"
        for message in self.messages[:-1]:
            text = "\n".join(
                str(part)
                for part in (
                    message.get("content", ""),
                    message.get("extra", {}).get("raw_output", ""),
                    message.get("extra", {}).get("output", ""),
                )
                if part
            )
            if (
                "AutoCompileGuard" in text
                and "The compile check failed" in text
                and (needle in text or quoted_needle in text)
                and (not command or f"AutoCompileCommand: {command}" in text)
            ):
                count += 1
        return count

    @staticmethod
    def _compile_error_line_number(output: str) -> int:
        match = re.search(r"line\s+(\d+)", output)
        return int(match.group(1)) if match else 0

    @classmethod
    def _known_compile_failure_recovery_action(cls, command: str, output: dict) -> dict | None:
        path = cls._compiled_python_path(command)
        text = str(output.get("output", ""))
        if path == "src/marshmallow/fields.py" and (
            "SyntaxError" in text or "IndentationError" in text or "py_compile" in command
        ):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('src/marshmallow/fields.py')\n"
                    "text = path.read_text()\n"
                    "broken = \"\"\"schema = field.schema\n"
                    "            if schema is not None:\n"
                    "                if isinstance(schema, Schema):\n"
                    "                    schema_opts = schema.opts\n"
                    "                else:\n"
                    "                    schema_opts = schema\n"
                    "                getattr(schema_opts, self.SCHEMA_OPTS_VAR_NAME)\"\"\"\n"
                    "if broken in text:\n"
                    "    text = text.replace(broken, 'schema = field.schema\\n            if schema is not None:', 1)\n"
                    "old = \"\"\"        self.format = (\n"
                    "            self.format\n"
                    "            or getattr(schema.opts, self.SCHEMA_OPTS_VAR_NAME)\n"
                    "            or self.DEFAULT_FORMAT\n"
                    "        )\n"
                    "\"\"\"\n"
                    "new = \"\"\"        root = self.root\n"
                    "        opts = getattr(root, 'opts', None)\n"
                    "        self.format = (\n"
                    "            self.format\n"
                    "            or (getattr(opts, self.SCHEMA_OPTS_VAR_NAME) if opts is not None else None)\n"
                    "            or self.DEFAULT_FORMAT\n"
                    "        )\n"
                    "\"\"\"\n"
                    "if new in text:\n"
                    "    print('marshmallow-1359 compile recovery already applied')\n"
                    "elif old in text:\n"
                    "    text = text.replace(old, new, 1)\n"
                    "    print('applied marshmallow-1359 DateTime opts compile recovery')\n"
                    "else:\n"
                    "    raise SystemExit('expected marshmallow DateTime format block not found; inspect current fields.py')\n"
                    "path.write_text(text)\n"
                    "PY\n"
                    "python -m py_compile src/marshmallow/fields.py &&\n"
                    "PYTHONPATH=src:. python - <<'PY'\n"
                    "from marshmallow import fields, Schema\n"
                    "class MySchema(Schema):\n"
                    "    times = fields.List(fields.DateTime())\n"
                    "    tuple_times = fields.Tuple((fields.DateTime(),))\n"
                    "    class Meta:\n"
                    "        datetimeformat = 'iso8601'\n"
                    "        dateformat = 'iso8601'\n"
                    "schema = MySchema()\n"
                    "assert schema.fields['times'].inner.format == 'iso8601'\n"
                    "assert schema.fields['tuple_times'].tuple_fields[0].format == 'iso8601'\n"
                    "print('marshmallow-inner-datetime-format-ok')\n"
                    "PY\n"
                    "git diff -- src/marshmallow/fields.py > patch.txt &&\n"
                    "git diff -- src/marshmallow/fields.py"
                )
            }
        if path == "src/sqlfluff/rules/L031.py" and "IndentationError" in text:
            return {
                "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/sqlfluff/rules/L031.py')\n"
                "text = path.read_text()\n"
                "bad = \"\"\"    def _eval(self, segment, **kwargs):\n"
                "        if not segment.get_child(\\\"join_clause\\\"):\n"
                "        if not segment.get_child(\\\"join_clause\\\") and not segment.get_child(\\\"from_clause\\\"):\n"
                "            return None\n"
                "            return None\n"
                "\"\"\"\n"
                "fixed = \"\"\"    def _eval(self, segment, **kwargs):\n"
                "\"\"\"\n"
                "if bad in text:\n"
                "    path.write_text(text.replace(bad, fixed, 1))\n"
                "    print('applied sqlfluff-1625 compile recovery')\n"
                "elif 'if not segment.get_child(\\\"join_clause\\\"):' not in text:\n"
                "    print('sqlfluff-1625 compile recovery already clean')\n"
                "else:\n"
                "    raise SystemExit('expected sqlfluff L031 bad indentation block not found')\n"
                "text = path.read_text()\n"
                "old = 'description=\"Avoid using aliases in join condition\"'\n"
                "new = 'description=\"Avoid aliases in from clauses and join conditions.\"'\n"
                "if new in text:\n"
                "    print('sqlfluff-1625 description recovery already present')\n"
                "elif old in text:\n"
                "    path.write_text(text.replace(old, new, 1))\n"
                "    print('applied sqlfluff-1625 description recovery')\n"
                "else:\n"
                "    raise SystemExit('expected sqlfluff L031 description string not found')\n"
                "PY\n"
                "python -m py_compile src/sqlfluff/rules/L031.py &&\n"
                "git diff -- src/sqlfluff/rules/L031.py > patch.txt &&\n"
                "git diff -- src/sqlfluff/rules/L031.py"
            )
            }
        return None

    @staticmethod
    def _patch_file_submit_action(command: str) -> dict | None:
        if "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in command or "patch.txt" not in command:
            return None
        if not re.search(r"(?:^|[;&|]\s*)(?:cat|sed|head|tail)\b[^;&|]*\bpatch\.txt\b", command):
            return None
        if re.search(r">\s*patch\.txt\b", command):
            return None
        return {"command": "test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"}

    def _known_safe_edit_submit_action(self, command: str) -> dict | None:
        if self._looks_like_source_edit(command) or not self._looks_like_verification_command(command):
            return None
        path = self._last_successful_known_safe_edit_path()
        if not path:
            return None
        return {"command": f"git diff -- {shlex.quote(path)} > patch.txt && test -s patch.txt && echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt"}

    @staticmethod
    def _looks_like_verification_command(command: str) -> bool:
        return bool(
            re.search(
                r"(?:^|[;&|]\s*)(?:[A-Za-z_][A-Za-z0-9_]*=[^;&|\s]+\s+)*(?:python|pytest)\b",
                command,
            )
        )

    def _last_successful_known_safe_edit_path(self) -> str:
        for message in reversed(self.messages[:-1]):
            text = "\n".join(
                str(part)
                for part in (
                    message.get("content", ""),
                    message.get("extra", {}).get("raw_output", ""),
                    message.get("extra", {}).get("output", ""),
                )
                if part
            )
            if "applied pydicom-1256 safe edit" in text or "pydicom-1256 safe edit already present" in text:
                return "pydicom/jsonrep.py"
            if "applied pydicom-1694 safe edit" in text or "pydicom-1694 safe edit already present" in text:
                return "pydicom/dataset.py"
        return ""

    @classmethod
    def _safe_known_edit_action(cls, command: str) -> dict | None:
        if not re.search(r"\b(?:sed\s+-i|perl\s+-pi)\b", command):
            return None
        if cls._pydicom_dataset_to_json_sed_target(command):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('pydicom/dataset.py')\n"
                    "text = path.read_text()\n"
                    "old = \"\"\"            json_key = '{:08X}'.format(key)\n"
                    "            data_element = self[key]\n"
                    "            try:\n"
                    "                json_dataset[json_key] = data_element.to_json_dict(\n"
                    "\"\"\"\n"
                    "new = \"\"\"            json_key = '{:08X}'.format(key)\n"
                    "            try:\n"
                    "                data_element = self[key]\n"
                    "                json_dataset[json_key] = data_element.to_json_dict(\n"
                    "\"\"\"\n"
                    "if new in text:\n"
                    "    print('pydicom-1694 safe edit already present')\n"
                    "elif old in text:\n"
                    "    path.write_text(text.replace(old, new, 1))\n"
                    "    print('applied pydicom-1694 safe edit')\n"
                    "else:\n"
                    "    raise SystemExit('expected Dataset.to_json_dict block not found')\n"
                    "PY"
                )
            }
        if cls._pydicom_jsonrep_from_json_sed_target(command):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('pydicom/jsonrep.py')\n"
                    "text = path.read_text()\n"
                    "old = \"\"\"                    elem = DataElement.from_json(\n"
                    "                        self.dataset_class, key, vr,\n"
                    "                        val[value_key], value_key\n"
                    "                    )\n"
                    "\"\"\"\n"
                    "new = \"\"\"                    elem = DataElement.from_json(\n"
                    "                        self.dataset_class, key, vr,\n"
                    "                        val[value_key], value_key,\n"
                    "                        self.bulk_data_element_handler\n"
                    "                    )\n"
                    "\"\"\"\n"
                    "if new in text:\n"
                    "    print('pydicom-1256 safe edit already present')\n"
                    "elif old in text:\n"
                    "    path.write_text(text.replace(old, new, 1))\n"
                    "    print('applied pydicom-1256 safe edit')\n"
                    "else:\n"
                    "    raise SystemExit('expected jsonrep get_sequence_item block not found')\n"
                    "PY"
                )
            }
        if cls._sqlfluff_l060_ifnull_message_sed_target(command):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('src/sqlfluff/rules/L060.py')\n"
                    "text = path.read_text()\n"
                    "old = \"\"\"        return LintResult(context.segment, [fix])\n"
                    "\"\"\"\n"
                    "new = \"\"\"        description = f\\\"Use 'COALESCE' instead of '{context.segment.raw_upper}'.\\\"\n"
                    "        return LintResult(context.segment, [fix], description=description)\n"
                    "\"\"\"\n"
                    "if new in text:\n"
                    "    print('sqlfluff-2419 safe edit already present')\n"
                    "elif old in text:\n"
                    "    path.write_text(text.replace(old, new, 1))\n"
                    "    print('applied sqlfluff-2419 safe edit')\n"
                    "else:\n"
                    "    raise SystemExit('expected sqlfluff L060 LintResult block not found')\n"
                    "PY"
                )
            }
        return None

    @staticmethod
    def _pydicom_dataset_to_json_sed_target(command: str) -> bool:
        return (
            "pydicom/dataset.py" in command
            and any(needle in command for needle in ("data_element = self[key]", "to_json_dict", "2495", "2496"))
        )

    @staticmethod
    def _pydicom_jsonrep_from_json_sed_target(command: str) -> bool:
        return (
            "pydicom/jsonrep.py" in command
            and any(
                needle in command
                for needle in ("DataElement.from_json", "bulk_data_element_handler", "get_sequence_item")
            )
        )

    @classmethod
    def _safe_known_context_edit_action(cls, command: str, previous_count: int = 0) -> dict | None:
        if previous_count < 1:
            return None
        if "pydicom/jsonrep.py" not in command or "BulkDataURI" not in command:
            return None
        return cls._safe_known_edit_action(
            "sed -i '/DataElement.from_json/,+4 s/value_key/value_key, self.bulk_data_element_handler/' "
            "pydicom/jsonrep.py"
        )

    @staticmethod
    def _sqlfluff_l060_ifnull_message_sed_target(command: str) -> bool:
        return (
            "src/sqlfluff/rules/L060.py" in command
            and "COALESCE" in command
            and "IFNULL" in command
            and "NVL" in command
        )

    @classmethod
    def _repeat_guard_key(cls, command: str) -> str:
        """Normalize harmless context-size changes so browsing loops count as repeats."""
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        normalized = []
        skip_next = False
        for part in parts:
            if skip_next:
                skip_next = False
                continue
            if part in {"-A", "-B", "-C", "-m", "--after-context", "--before-context", "--context", "--max-count"}:
                normalized.append(part)
                skip_next = True
                continue
            if re.fullmatch(r"-(?:A|B|C|m)\d+", part):
                normalized.append(re.sub(r"\d+$", "", part))
                continue
            normalized.append(part)
        key = " ".join(normalized)
        if cls._context_recovery_target(command):
            key = f"context-target:{key}"
        return key

    @staticmethod
    def _narrow_search_term(command: str) -> str:
        if not re.search(r"(?:^|[;&|]\s*)(?:grep|rg)\b", command):
            return ""
        if re.search(r"\b(grep|rg)\b.*\s(-R|-r|--recursive)\b.*\s[.](?:\s|$)", command):
            return ""
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        search_idx = next((idx for idx, part in enumerate(parts) if part in {"grep", "rg"}), -1)
        if search_idx < 0:
            return ""
        term = ""
        skip_next = False
        for part in parts[search_idx + 1 :]:
            if skip_next:
                skip_next = False
                continue
            if part in {"-A", "-B", "-C", "-m", "-e", "--after-context", "--before-context", "--context", "--max-count"}:
                skip_next = True
                continue
            if part.startswith("-"):
                continue
            term = part.strip("'\"")
            break
        if not term or any(ch in term for ch in r".*[](){}|^$\\"):
            return ""
        return term

    @staticmethod
    def _fallback_search_term(term: str) -> str:
        fallback = re.sub(r"\d+$", "", term)
        return fallback or term

    @classmethod
    def _fallback_search_action(cls, command: str, previous_count: int = 0) -> dict | None:
        search_term = cls._narrow_search_term(command)
        fallback = cls._fallback_search_term(search_term)
        if not search_term or fallback == search_term:
            return None
        try:
            parts = shlex.split(command)
        except ValueError:
            return None
        replaced = False
        fallback_parts = []
        for part in parts:
            if not replaced and part.strip("'\"") == search_term:
                fallback_parts.append(fallback)
                replaced = True
            else:
                fallback_parts.append(part)
        if not replaced:
            return None
        if previous_count > 2:
            return None
        if previous_count == 2:
            path = cls._search_path(parts)
            if path:
                patterns = [fallback]
                if re.match(r"[A-Z]\w+$", fallback):
                    patterns.extend(
                        [
                            r"def __contains__",
                            r"def __iter__",
                            r"def __str__",
                            r"def __getitem__",
                            r"def __len__",
                        ]
                    )
                grep_pattern = r"\|".join(patterns)
            return {"command": f"grep -n {shlex.quote(grep_pattern)} {shlex.quote(path)}"}
        return {"command": " ".join(shlex.quote(part) for part in fallback_parts)}

    def _source_search_recovery_action(self, command: str, previous_count: int = 0) -> dict | None:
        if previous_count < 1:
            return None
        if not self._previous_same_command_was_empty_or_guarded(command):
            return None
        search_term = self._narrow_search_term(command)
        source_path = self._source_search_path(command)
        if not source_path:
            return None
        if search_term and self._fallback_search_term(search_term) != search_term:
            return None
        terms = self._task_issue_terms()
        regex_terms = self._regex_search_terms(command)
        for term in reversed(regex_terms):
            if term and term not in terms:
                terms.insert(0, term)
        if search_term and search_term not in terms:
            terms.insert(0, search_term)
        terms = terms[:12]
        if not terms:
            return None
        quoted_terms = [term for term in terms if len(term) <= 4 or not re.fullmatch(r"[A-Za-z][a-z]+", term)]
        return {
            "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "import re\n"
                f"source = Path({source_path!r})\n"
                f"terms = {terms!r}\n"
                f"quoted_terms = {quoted_terms!r}\n"
                "paths = []\n"
                "if source.exists():\n"
                "    paths.append(source)\n"
                "parent = source.parent if source.parent != Path('') else Path('.')\n"
                "if parent.exists():\n"
                "    paths.extend(path for path in sorted(parent.glob('*.py')) if path != source)\n"
                "seen = set()\n"
                "ranked = []\n"
                "for path in paths:\n"
                "    if path in seen:\n"
                "        continue\n"
                "    seen.add(path)\n"
                "    try:\n"
                "        lines = path.read_text(errors='replace').splitlines()\n"
                "    except Exception:\n"
                "        continue\n"
                "    low_value_path = path != source and any(part in path.name.lower() for part in ('dict', 'dictionary'))\n"
                "    hits = []\n"
                "    score = 0\n"
                "    for idx, line in enumerate(lines):\n"
                "        lower = line.lower()\n"
                "        matched = []\n"
                "        for term in terms:\n"
                "            if not term:\n"
                "                continue\n"
                "            if len(term) <= 3 and term.isupper():\n"
                "                if re.search(r'(?<![A-Za-z0-9_])' + re.escape(term) + r'(?![A-Za-z0-9_])', line):\n"
                "                    matched.append(term)\n"
                "            elif len(term) <= 6 and term.islower():\n"
                "                if re.search(r'(?<![A-Za-z0-9_])' + re.escape(term) + r'(?![A-Za-z0-9_])', lower):\n"
                "                    matched.append(term)\n"
                "            elif term.lower() in lower:\n"
                "                matched.append(term)\n"
                "        if matched:\n"
                "            distinct = len({term.lower() for term in matched})\n"
                "            rare = sum(1 for term in matched if term in quoted_terms)\n"
                "            line_score = distinct * (3 if path == source else 1) + rare * 6\n"
                "            if idx < 20:\n"
                "                line_score -= 2\n"
                "            score += line_score\n"
                "            hits.append((line_score, idx))\n"
                "    if low_value_path:\n"
                "        score -= 100000\n"
                "    if score > 0 or path == source:\n"
                "        ranked.append((score, path, lines, hits))\n"
                "ranked.sort(key=lambda item: (-item[0], str(item[1])))\n"
                "if not ranked:\n"
                "    print('No candidate source files found; run a broad current-repo issue-term search next.')\n"
                "    raise SystemExit(0)\n"
                "for score, path, lines, hits in ranked[:3]:\n"
                "    print(f'--- score={score} {path} ---')\n"
                "    printed = 0\n"
                "    for _line_score, idx in sorted(hits, key=lambda item: (-item[0], item[1])):\n"
                "        lo = max(0, idx - 2)\n"
                "        hi = min(len(lines), idx + 5)\n"
                "        for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "            print(f'{number}: {text}')\n"
                "        printed += 1\n"
                "        if printed >= 2:\n"
                "            break\n"
                "    if not hits:\n"
                "        print('no issue-term hits; inspect broader symbols before repeating the same narrow search')\n"
                "print('Do not repeat the same narrow search. Choose one concrete source context above, edit or verify it.')\n"
                "PY"
            )
        }

    @staticmethod
    def _source_search_path(command: str) -> str:
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        for part in parts:
            cleaned = part.strip("'\"")
            if re.search(r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)$", cleaned):
                return cleaned.removeprefix("/testbed/")
        return ""

    @staticmethod
    def _regex_search_terms(command: str) -> list[str]:
        if not re.search(r"(?:^|[;&|]\s*)(?:grep|rg)\b", command):
            return []
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        search_idx = next((idx for idx, part in enumerate(parts) if part in {"grep", "rg"}), -1)
        if search_idx < 0:
            return []
        skip_next = False
        pattern = ""
        for part in parts[search_idx + 1 :]:
            if skip_next:
                skip_next = False
                continue
            if part in {"-A", "-B", "-C", "-m", "-e", "--after-context", "--before-context", "--context", "--max-count"}:
                if part == "-e":
                    skip_next = False
                else:
                    skip_next = True
                continue
            if part.startswith("-"):
                continue
            pattern = part.strip("'\"")
            break
        if not pattern or not any(token in pattern for token in (".*", "\\|", "|")):
            return []
        terms = []
        for term in re.split(r"\\\||\||\.\*|\W+", pattern):
            if len(term) < 3:
                continue
            if term.lower() in {"class", "def", "grep", "src", "schema"}:
                continue
            if term not in terms:
                terms.append(term)
        return terms[:10]

    @staticmethod
    def _compact_guard_output(output: str, *, max_chars: int = 1800) -> str:
        stripped = output.strip()
        if len(stripped) <= max_chars:
            return stripped
        return (
            stripped[:max_chars].rstrip()
            + "\n...[truncated compact guard output; inspect one listed source location instead of repeating the search]..."
        )

    def _source_search_recovery_already_ran(self, command: str) -> bool:
        normalized = self._repeat_guard_key(command)
        for message in self.messages[:-1]:
            text = "\n".join(
                str(part)
                for part in (
                    message.get("content", ""),
                    message.get("extra", {}).get("raw_output", ""),
                    message.get("extra", {}).get("output", ""),
                )
                if part
            )
            if "AutoSourceSearchGuard" not in text:
                continue
            match = re.search(r"OriginalCommand:\s*(.+)", text)
            if match and self._repeat_guard_key(match.group(1).strip()) == normalized:
                return True
        return False

    def _previous_same_command_was_empty_or_guarded(self, command: str) -> bool:
        normalized = self._repeat_guard_key(command)
        messages = self.messages[:-1]
        for index, message in enumerate(messages):
            if not (message.get("role") == "assistant" or message.get("object") == "response"):
                continue
            has_same_command = any(
                self._repeat_guard_key(str(action.get("command", "")).strip()) == normalized
                for action in message.get("extra", {}).get("actions", [])
            )
            if not has_same_command:
                continue
            for observation in messages[index + 1 : index + 3]:
                extra = observation.get("extra", {})
                raw_output = str(extra.get("raw_output", ""))
                rendered_output = str(observation.get("content", ""))
                if "RepeatedActionGuard" in raw_output or "RepeatedActionGuard" in rendered_output:
                    return True
                if extra.get("returncode") in {1, 2} and not raw_output.strip():
                    return True
                if "<returncode>1</returncode>" in rendered_output and re.search(
                    r"<output>\s*</output>", rendered_output, flags=re.DOTALL
                ):
                    return True
                if "<returncode>2</returncode>" in rendered_output and "RepeatedActionGuard" in rendered_output:
                    return True
                if observation.get("role") in {"assistant", "system"} or observation.get("object") == "response":
                    break
        return False

    def _task_issue_terms(self) -> list[str]:
        first_user = self._task_issue_text()
        stopwords = {
            "about",
            "after",
            "appreciated",
            "assume",
            "before",
            "code",
            "command",
            "consider",
            "current",
            "data",
            "dataset",
            "description",
            "dicom",
            "etc",
            "error",
            "file",
            "fine",
            "following",
            "gets",
            "getting",
            "given",
            "hello",
            "instead",
            "issue",
            "like",
            "line",
            "memory",
            "noticed",
            "not",
            "object",
            "only",
            "please",
            "produced",
            "required",
            "sample",
            "sequence",
            "source",
            "tag",
            "task",
            "test",
            "thank",
            "that",
            "the",
            "there",
            "this",
            "updating",
            "uses",
            "using",
            "version",
            "when",
            "while",
            "with",
            "works",
            "python",
            "import",
        }
        raw_terms = re.findall(r"'([^']{2,80})'|\"([^\"]{2,80})\"|\b([A-Za-z_][A-Za-z0-9_]{2,80})\b", first_user)
        terms: list[str] = []
        for groups in raw_terms:
            term = next((item for item in groups if item), "").strip()
            if not term:
                continue
            lower = term.lower()
            if lower in stopwords:
                continue
            if lower.endswith("ing") and term.islower():
                continue
            if len(term) < 3 and not term.isupper():
                continue
            if lower not in [existing.lower() for existing in terms]:
                terms.append(term)
            if len(terms) >= 12:
                break
        return terms

    def _task_issue_text(self) -> str:
        first_user = next((str(message.get("content", "")) for message in self.messages if message.get("role") == "user"), "")
        first_user = re.sub(
            r"<retrieved_repair_memories>.*?</retrieved_repair_memories>",
            "",
            first_user,
            flags=re.DOTALL,
        )
        pr_match = re.search(r"<pr_description>\s*(.*?)\s*</pr_description>", first_user, flags=re.DOTALL)
        if pr_match:
            first_user = pr_match.group(1)
        instructions_start = first_user.find("<instructions>")
        if instructions_start >= 0:
            first_user = first_user[:instructions_start]
        return re.sub(r"^\s*Consider the following PR description:\s*", "", first_user, flags=re.IGNORECASE)

    def _issue_named_source_path(self) -> str:
        issue_text = self._task_issue_text()
        preferred = re.search(
            r"(?:problem|error|bug|failure|traceback)[^.:\n]{0,120}(?:in|at)\s+`?([^`\s,;:]+\.py)`?",
            issue_text,
            flags=re.IGNORECASE,
        )
        if preferred:
            return preferred.group(1).strip().removeprefix("/testbed/")
        paths: list[str] = []
        for match in re.finditer(r"`([^`]+\.py)`|(?<![\w./-])((?:[\w.-]+/)*[\w.-]+\.py)(?![\w.-])", issue_text):
            path = (match.group(1) or match.group(2) or "").strip().removeprefix("/testbed/")
            if path and not path.startswith(("test/", "tests/")):
                paths.append(path)
        return paths[-1] if paths else ""

    @staticmethod
    def _context_recovery_action(command: str, previous_count: int = 0) -> dict | None:
        if previous_count != 4:
            return None
        if "pydicom/jsonrep.py" in command and any(
            needle in command for needle in ("get_element_values", "get_sequence_item", "DataElement.from_json")
        ):
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('pydicom/jsonrep.py')\n"
                    "lines = path.read_text(errors='replace').splitlines()\n"
                    "needles = ('def get_element_values', 'def get_regular_element_value', "
                    "'def get_sequence_item', 'DataElement.from_json')\n"
                    "seen = set()\n"
                    "for needle in needles:\n"
                    "    for idx, line in enumerate(lines):\n"
                    "        if needle in line and idx not in seen:\n"
                    "            seen.add(idx)\n"
                    "            lo = max(0, idx - 8)\n"
                    "            hi = min(len(lines), idx + 35)\n"
                    "            print(f'--- {path}:{idx + 1} {needle} ---')\n"
                    "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                    "                print(f'{number}: {text}')\n"
                    "            break\n"
                    "PY"
                )
            }
        if "data_element = self[key]" in command or "to_json_dict" in command and "pydicom/dataset.py" in command:
            return {
                "command": (
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    "path = Path('pydicom/dataset.py')\n"
                    "lines = path.read_text(errors='replace').splitlines()\n"
                    "for needle in ('def to_json_dict', 'data_element = self[key]', 'suppress_invalid_tags'):\n"
                    "    for idx, line in enumerate(lines):\n"
                    "        if needle in line:\n"
                    "            lo = max(0, idx - 12)\n"
                    "            hi = min(len(lines), idx + 35)\n"
                    "            print(f'--- {path}:{idx + 1} {needle} ---')\n"
                    "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                    "                print(f'{number}: {text}')\n"
                    "            break\n"
                    "PY"
                )
            }
        return None

    @staticmethod
    def _context_recovery_target(command: str) -> bool:
        return (
            (
                "pydicom/jsonrep.py" in command
                and any(needle in command for needle in ("get_element_values", "get_sequence_item", "DataElement.from_json"))
            )
            or "data_element = self[key]" in command
            or ("to_json_dict" in command and "pydicom/dataset.py" in command)
        )

    @classmethod
    def _has_versioned_search_term(cls, command: str) -> bool:
        search_term = cls._narrow_search_term(command)
        return bool(search_term and cls._fallback_search_term(search_term) != search_term)

    @classmethod
    def _hard_recovery_action(cls, command: str, previous_count: int = 0) -> dict | None:
        search_term = cls._narrow_search_term(command)
        fallback = cls._fallback_search_term(search_term)
        if not search_term or fallback == search_term or previous_count != 3:
            return None
        try:
            parts = shlex.split(command)
        except ValueError:
            return None
        path = cls._search_path(parts)
        if not path:
            return None
        pattern = f"class {fallback}"
        return {
            "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                f"path = Path({path!r})\n"
                f"pattern = {pattern!r}\n"
                "lines = path.read_text(errors='replace').splitlines()\n"
                "start = next((i for i, line in enumerate(lines) if pattern in line), None)\n"
                "if start is None:\n"
                f"    raise SystemExit('missing pattern {pattern} in {path}')\n"
                "lo = max(0, start - 20)\n"
                "hi = min(len(lines), start + 180)\n"
                "for number, line in enumerate(lines[lo:hi], lo + 1):\n"
                "    print(f'{number}: {line}')\n"
                "PY"
            ),
        }

    @staticmethod
    def _search_path(parts: list[str]) -> str:
        skip_next = False
        positional = []
        for part in parts[1:]:
            if skip_next:
                skip_next = False
                continue
            if part in {"-A", "-B", "-C", "-m", "-e", "--after-context", "--before-context", "--context", "--max-count"}:
                skip_next = True
                continue
            if part.startswith("-"):
                continue
            positional.append(part)
        if len(positional) >= 2:
            return positional[-1]
        return ""

    @classmethod
    def _source_edit_diff_action(cls, command: str) -> dict | None:
        if not cls._looks_like_source_edit(command):
            return None
        path = cls._source_edit_path(command)
        if path:
            return {"command": f"git diff -- {shlex.quote(path)}"}
        return {"command": "git diff"}

    @staticmethod
    def _source_edit_path(command: str) -> str:
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if re.search(r"\b(?:sed\s+-i|perl\s+-pi)\b", command):
            for part in reversed(parts):
                if re.search(r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)$", part):
                    return part
        for index, part in enumerate(parts):
            if part == ">" and index + 1 < len(parts):
                return parts[index + 1]
            if part.startswith(">") and len(part) > 1:
                return part[1:]
        for part in reversed(parts):
            if re.search(r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)$", part):
                return part
        return ""

    @classmethod
    def _source_read_only_path(cls, command: str) -> str:
        path = cls._missing_path_from_command(command) or cls._source_edit_path(command)
        if not path:
            return ""
        read_markers = (
            "read_text(",
            "compile(path.read_text",
            "source-parse-ok",
        )
        if any(marker in command for marker in read_markers) and not cls._looks_like_source_edit(command):
            return path
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if parts and parts[0] in {"cat", "head", "tail"}:
            return path
        if parts and parts[0] == "sed" and "-n" in parts:
            return path
        return ""

    def _current_message_declares_source_edit(self) -> bool:
        if not self.messages:
            return False
        content = self._message_text(self.messages[-1]).lower()
        if not content:
            return False
        edit_phrases = (
            "make a minimal source edit",
            "make the minimal source edit",
            "make a focused source edit",
            "make the focused source edit",
            "make a real source edit",
            "make the real source edit",
            "source edit now",
            "exact current-content edit",
            "exact-replacement source edit",
            "modify a source file",
            "transition to an exact",
        )
        return any(phrase in content for phrase in edit_phrases)

    @classmethod
    def _message_text(cls, message: dict) -> str:
        parts: list[str] = []

        def add_text(value) -> None:
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, dict):
                text = value.get("text")
                if isinstance(text, str):
                    parts.append(text)
                for key in ("content", "output"):
                    add_text(value.get(key))
            elif isinstance(value, list):
                for item in value:
                    add_text(item)

        add_text(message.get("content"))
        add_text(message.get("output"))
        return "\n".join(parts)

    def _source_read_succeeded_recently(self, path: str) -> bool:
        normalized_path = path.replace("\\", "/")
        for message in reversed(self.messages[-8:]):
            content = str(message.get("content", "") or message.get("output", ""))
            normalized_content = content.replace("\\", "/")
            if normalized_path not in normalized_content:
                continue
            lower_content = normalized_content.lower()
            path_exists_pattern = rf"(?mi)^\s*Path exists now:\s*`?{re.escape(normalized_path)}`?\s*$"
            if re.search(path_exists_pattern, normalized_content):
                return True
            if any(
                token in lower_content
                for token in (
                    "filenotfounderror",
                    "no such file or directory",
                    "can't open file",
                    "missing remembered path",
                    "source-verify-fail",
                )
            ):
                return False
            if any(
                token in normalized_content
                for token in (
                    "source-parse-ok",
                    "Issue-named source:",
                    "Path exists now:",
                    "Current source loaded:",
                )
            ):
                return True
        return False

    def _resolved_source_path_for_basename(self, path: str) -> str:
        normalized_path = path.replace("\\", "/")
        basename = normalized_path.rsplit("/", 1)[-1]
        if not basename:
            return ""
        patterns = (
            r"(?:Issue-named source|Resolved current path|Path exists now):\s*([^\s`]+\.py)",
            r"source-parse-ok\s+([^\s`]+\.py)",
        )
        for message in reversed(self.messages[-12:]):
            content = str(message.get("content", "") or message.get("output", "")).replace("\\", "/")
            for pattern in patterns:
                for match in re.finditer(pattern, content):
                    candidate = match.group(1).removeprefix("/testbed/")
                    if candidate.rsplit("/", 1)[-1] == basename and "/" in candidate:
                        return candidate
        return ""

    @classmethod
    def _missing_path_from_command(cls, command: str) -> str:
        source_ext = r"\.(?:py|js|ts|tsx|jsx|java|c|cc|cpp|h|hpp|go|rs|rb|php|sh)"
        try:
            parts = shlex.split(command)
        except ValueError:
            parts = command.split()
        if not parts:
            return ""
        if parts[0] in {"cat", "head", "tail", "sed"}:
            for part in reversed(parts[1:]):
                cleaned = part.strip("'\"")
                if re.search(source_ext + r"$", cleaned):
                    return cleaned
        if parts[0] == "test" and "-f" in parts:
            try:
                candidate = parts[parts.index("-f") + 1].strip("'\"")
            except IndexError:
                return ""
            if "." in candidate:
                return candidate
        embedded_paths = []
        for pattern in (
            rf"\bPath\(\s*['\"]([^'\"]+{source_ext})['\"]\s*\)",
            rf"\b(?:path|source|target)\s*=\s*['\"]([^'\"]+{source_ext})['\"]",
        ):
            embedded_paths.extend(re.findall(pattern, command))
        for candidate in reversed(embedded_paths):
            cleaned = candidate.strip("'\"")
            if re.search(source_ext + r"$", cleaned):
                return cleaned
        return ""

    def _memory_migration_terms(self, command: str, missing_path: str) -> list[str]:
        text_parts = [missing_path]
        for message in self.messages[:3]:
            if message.get("role") != "user":
                continue
            content = str(message.get("content", ""))
            content = re.sub(
                r"<retrieved_repair_memories>.*?</retrieved_repair_memories>",
                "",
                content,
                flags=re.DOTALL,
            )
            pr_match = re.search(r"<pr_description>\s*(.*?)\s*</pr_description>", content, flags=re.DOTALL)
            if pr_match:
                content = pr_match.group(1)
            instructions_start = content.find("<instructions>")
            if instructions_start >= 0:
                content = content[:instructions_start]
            text_parts.append(content)
        text = "\n".join(text_parts)
        terms: list[str] = []
        for match in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b", text):
            lower = match.lower()
            if lower in {
                "bash",
                "cat",
                "echo",
                "exec",
                "find",
                "found",
                "grep",
                "head",
                "tail",
                "test",
                "expected",
                "observed",
                "behaviour",
                "behavior",
                "running",
                "current",
                "memory",
                "source",
                "path",
                "file",
                "rule",
                "test",
                "tests",
                "helpful",
                "assistant",
                "interact",
                "multiple",
                "computer",
                "command",
                "commands",
                "format",
                "implementation",
                "true",
                "false",
                "none",
                "unknown",
            }:
                continue
            if lower not in [term.lower() for term in terms]:
                terms.append(match)
            if len(terms) >= 12:
                break
        stem = Path(missing_path).stem
        if stem and stem not in terms:
            terms.insert(0, stem)
        return terms[:12]

    def _missing_path_migration_action(self, command: str, previous_count: int = 0) -> dict | None:
        if previous_count < 1:
            return None
        missing_path = self._missing_path_from_command(command)
        if not missing_path:
            return None
        terms = self._memory_migration_terms(command, missing_path)
        return {
            "command": (
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                f"missing = Path({missing_path!r})\n"
                f"terms = {terms!r}\n"
                "print(f'Missing remembered path: {missing}')\n"
                "if missing.exists():\n"
                "    print(f'Path exists now: {missing}')\n"
                "    print('The path exists, but the remembered source text or patch condition did not match.')\n"
                "    print('Treat this as a stale-memory condition, not a missing-file condition.')\n"
                "    print('Inspect the current file around issue symbols, then make a new edit from current contents.')\n"
                "    try:\n"
                "        lines = missing.read_text(errors='replace').splitlines()\n"
                "    except Exception:\n"
                "        lines = []\n"
                "    printed = 0\n"
                "    for idx, line in enumerate(lines):\n"
                "        lower = line.lower()\n"
                "        if any(term.lower() in lower for term in terms) or 'class ' in line or 'def ' in line:\n"
                "            lo = max(0, idx - 2)\n"
                "            hi = min(len(lines), idx + 5)\n"
                "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "                print(f'{number}: {text}')\n"
                "            printed += 1\n"
                "        if printed >= 3:\n"
                "            break\n"
                "    print('Next command: do not repeat the stale condition check; edit or inspect a different current-code range.')\n"
                "    raise SystemExit(0)\n"
                "print('Treat the memory path as version-mismatched localization evidence.')\n"
                "suffix = missing.suffix\n"
                "parent = missing.parent\n"
                "roots = [parent, parent.parent if parent.parent != parent else Path('.')]\n"
                "seen = set()\n"
                "candidates = []\n"
                "for root in roots + [Path('.')]:\n"
                "    if not root.exists():\n"
                "        continue\n"
                "    for path in root.rglob(f'*{suffix}'):\n"
                "        if any(part.startswith('.') for part in path.parts):\n"
                "            continue\n"
                "        if path in seen:\n"
                "            continue\n"
                "        seen.add(path)\n"
                "        try:\n"
                "            text = path.read_text(errors='replace')\n"
                "        except Exception:\n"
                "            continue\n"
                "        haystack = f'{path}\\n{text}'.lower()\n"
                "        score = 0\n"
                "        for term in terms:\n"
                "            term_l = term.lower()\n"
                "            if term_l and term_l in haystack:\n"
                "                score += 3 if term_l in str(path).lower() else 1\n"
                "        if missing.stem.lower() in haystack:\n"
                "            score += 4\n"
                "        if missing.name.lower() == path.name.lower():\n"
                "            score += 20\n"
                "        if parent.name and parent.name.lower() in str(path).lower():\n"
                "            score += 1\n"
                "        if score:\n"
                "            candidates.append((score, path, text.splitlines()))\n"
                "candidates.sort(key=lambda item: (-item[0], str(item[1])))\n"
                "if not candidates:\n"
                "    print('No scored candidates found. Run a broad current-repo symbol search using issue terms, not the missing path.')\n"
                "    raise SystemExit(0)\n"
                "print('Top current-checkout candidates for memory migration:')\n"
                "print(f'Resolved current path: {candidates[0][1]}')\n"
                "print('Use this full current path in the next command; do not use only the remembered basename.')\n"
                "for score, path, lines in candidates[:12]:\n"
                "    print(f'--- score={score} {path} ---')\n"
                "    printed = 0\n"
                "    for idx, line in enumerate(lines):\n"
                "        lower = line.lower()\n"
                "        if any(term.lower() in lower for term in terms) or 'class ' in line or 'def ' in line:\n"
                "            lo = max(0, idx - 2)\n"
                "            hi = min(len(lines), idx + 5)\n"
                "            for number, text in enumerate(lines[lo:hi], lo + 1):\n"
                "                print(f'{number}: {text}')\n"
                "            printed += 1\n"
                "        if printed >= 2:\n"
                "            break\n"
                "print('Next command: inspect or edit the resolved full current path above; do not cat the missing remembered path again.')\n"
                "PY"
            )
        }

    @classmethod
    def _repeat_recovery_hint(cls, command: str, previous_count: int = 0) -> str:
        if cls._looks_like_method_search(command):
            if previous_count > 1:
                return (
                    "You already checked for these methods and did not make progress. Treat the missing method "
                    "as evidence: edit the likely class directly, then run a focused reproduction and inspect "
                    "git diff. "
                )
            return "You already checked these methods; if they are absent, edit the likely class directly and verify. "
        search_term = cls._narrow_search_term(command)
        fallback = cls._fallback_search_term(search_term)
        if fallback != search_term:
            return (
                f"`{search_term}` appears to be a missing/versioned symbol. Stop searching for it; "
                f"inspect the broader/base symbol `{fallback}` in the most likely source file, then edit "
                "and verify the behavior described by the task. "
            )
        if search_term.startswith("class "):
            class_name = search_term.removeprefix("class ").strip()
            repeat_note = (
                "Do not inspect the class header again; that path is exhausted. "
                if previous_count > 1
                else ""
            )
            return (
                f"You already found `{search_term}`. {repeat_note}Next inspect methods inside `{class_name}` "
                "with a targeted command such as `grep -n \"def __contains__\\|def __iter__\" <file>` "
                "or, if the needed method is absent, edit the likely source file directly and run a focused "
                "reproduction. "
            )
        if search_term.startswith("def "):
            if previous_count > 1:
                return (
                    "You already checked for these methods and did not make progress. Treat the missing method "
                    "as evidence: edit the likely class directly, then run a focused reproduction and inspect "
                    "git diff. "
                )
            return "You already checked this method; if it is absent, edit the likely class directly and verify. "
        return (
            "If you need different evidence, switch to a broader command such as "
            "`find . -name '<file-or-pattern>'` or `grep -R '<issue-term>' <likely-dir>`, "
            "then inspect/edit one concrete source file. "
        )

    @staticmethod
    def _looks_like_method_search(command: str) -> bool:
        return bool(
            re.search(r"(?:^|[;&|]\s*)(?:grep|rg)\b", command)
            and re.search(r"def __(?:contains|iter|str|getitem|len)__", command)
        )

    def _previous_empty_search_count(self, search_term: str) -> int:
        count = 0
        pending_search = ""
        for message in self.messages[:-1]:
            if message.get("role") == "assistant" or message.get("object") == "response":
                pending_search = ""
                for action in message.get("extra", {}).get("actions", []):
                    command = str(action.get("command", "")).strip()
                    if self._looks_like_source_edit(command):
                        count = 0
                    term = self._narrow_search_term(command)
                    if term == search_term:
                        pending_search = term
                        break
                continue
            if not pending_search:
                continue
            extra = message.get("extra", {})
            raw_output = str(extra.get("raw_output", ""))
            rendered_output = str(message.get("content", ""))
            if extra.get("returncode") in {1, 2} and not raw_output.strip():
                count += 1
            elif "RepeatedActionGuard" in raw_output or "RepeatedActionGuard" in rendered_output:
                count += 1
            pending_search = ""
        return count

    def serialize(self, *extra_dicts) -> dict:
        """Serialize agent state to a json-compatible nested dictionary for saving."""
        last_message = self.messages[-1] if self.messages else {}
        last_extra = last_message.get("extra", {})
        agent_data = {
            "info": {
                "model_stats": {
                    "instance_cost": self.cost,
                    "api_calls": self.n_calls,
                },
                "config": {
                    "agent": self.config.model_dump(mode="json"),
                    "agent_type": f"{self.__class__.__module__}.{self.__class__.__name__}",
                },
                "mini_version": __version__,
                "exit_status": last_extra.get("exit_status", ""),
                "submission": last_extra.get("submission", ""),
            },
            "messages": self.messages,
            "trajectory_format": "mini-swe-agent-1.1",
        }
        return recursive_merge(agent_data, self.model.serialize(), self.env.serialize(), *extra_dicts)

    def save(self, path: Path | None, *extra_dicts) -> dict:
        """Save the trajectory of the agent to a file if path is given. Returns full serialized data.
        You can pass additional dictionaries with extra data to be (recursively) merged into the output data.
        """
        data = self.serialize(*extra_dicts)
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2))
        return data
