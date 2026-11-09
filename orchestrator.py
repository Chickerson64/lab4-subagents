"""
Agent-driven orchestration with file-defined specialists.

Each Markdown file in .claude/subagents/ must contain YAML frontmatter:

---
name: agent-name
description: When the orchestrator should use this agent.
tools:
  - Read
  - Glob
  - Grep
---

The Markdown body is the agent's complete system prompt.

Running this script can modify project files if a specialist has
Write or Edit access.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

def load_claude_runtime():
    # The optional coding runtime is independent of the stdlib learning program.
    global AgentDefinition, AssistantMessage, ClaudeAgentOptions
    global ResultMessage, TextBlock, ToolUseBlock, query
    try:
        from claude_agent_sdk import (
            AgentDefinition, AssistantMessage, ClaudeAgentOptions,
            ResultMessage, TextBlock, ToolUseBlock, query,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Optional Claude runtime unavailable. Use python3 -m src.train "
            "for Lab 5 or python3 orchestrator.py --demo-hooks for local hooks. "
            "No Claude API call was made."
        ) from exc
    if yaml is None:
        raise RuntimeError("Optional Claude runtime also requires PyYAML.")



PROJECT_ROOT = Path(__file__).resolve().parent

# Runtime policy, not specialist configuration.
# Bash is intentionally excluded: agents cannot execute shell commands.
SUPPORTED_TOOLS = frozenset({
    "Read",
    "Glob",
    "Grep",
    "Write",
    "Edit",
    "Skill",
})

PARENT_TOOLS = ["Agent", "Read", "Glob", "Grep","Skill"]

ORCHESTRATOR_POLICY = """
You are the lead orchestration agent for this repository.

Your responsibility is to plan, delegate, inspect results, coordinate
revisions, and synthesize the final answer.

Use the registered specialist descriptions to choose agents.
Do not assume a fixed workflow or fixed specialist names.

Rules:
1. Delegate substantive implementation and review to specialists.
   Do not implement source files yourself.
2. Inspect only enough repository context to understand the request.
3. Give every delegation a focused, self-contained prompt containing:
   - the concrete objective;
   - relevant file paths;
   - required inputs and public interface contracts;
   - acceptance criteria;
   - the expected report.
4. Pass only information relevant to the specialist's assignment.
   Do not forward the full conversation or unrelated specialist reports.
5. Use fresh, non-fork subagents for independent assignments.
6. Wait for a specialist's result before starting dependent work.
   Parallelize only genuinely independent tasks.
7. Resolve interface contracts before delegating dependent implementations.
8. When a suitable reviewer is registered, request independent review of
   the actual artifacts before declaring implementation work complete.
9. Delegate targeted fixes when review identifies defects.
   Allow at most two repair-and-review cycles, then report remaining issues.
10. Never claim that a tool call, file change, review, or test happened
    unless the execution results support that claim.
11. If tools or requirements are insufficient, report the blocker.
12. Do not modify agent specifications or runtime configuration.

Final report:
- Work completed
- Files created or changed
- Important decisions and assumptions
- Review findings
- Tests actually executed
- Unresolved issues

A successful runtime exit does not by itself establish project correctness.
"""


def required_string(
    metadata: dict[str, Any],
    field: str,
    path: Path,
) -> str:
    value = metadata.get(field)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{path}: '{field}' must be a non-empty string."
        )

    return value.strip()


def parse_tools(value: Any, path: Path) -> list[str]:
    if isinstance(value, str):
        tools = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        tools = value
    else:
        raise ValueError(
            f"{path}: 'tools' must be a YAML list or comma-separated string."
        )

    if not all(isinstance(tool, str) and tool.strip() for tool in tools):
        raise ValueError(
            f"{path}: every tool must be a non-empty string."
        )

    tools = list(dict.fromkeys(tool.strip() for tool in tools))

    unsupported = set(tools) - SUPPORTED_TOOLS
    if unsupported:
        raise ValueError(
            f"{path}: tools not permitted by this runtime: "
            f"{', '.join(sorted(unsupported))}. "
            f"Permitted tools: {', '.join(sorted(SUPPORTED_TOOLS))}."
        )

    return tools


def load_agent(path: Path) -> tuple[str, AgentDefinition]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError(
            f"{path}: missing YAML frontmatter. "
            "Add name, description, and tools above the Markdown body."
        )

    closing = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        ),
        None,
    )

    if closing is None:
        raise ValueError(f"{path}: YAML frontmatter is not closed.")

    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc

    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: frontmatter must be a YAML mapping.")

    # Fail rather than silently ignore unsupported configuration.
    allowed_fields = {"name", "description", "tools", "model"}
    unknown_fields = set(metadata) - allowed_fields

    if unknown_fields:
        raise ValueError(
            f"{path}: unsupported frontmatter fields: "
            f"{', '.join(sorted(map(str, unknown_fields)))}."
        )

    name = required_string(metadata, "name", path)
    description = required_string(metadata, "description", path)

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError(
            f"{path}: 'name' must use lowercase letters, digits, and hyphens."
        )

    tools = parse_tools(metadata.get("tools"), path)
    prompt = "\n".join(lines[closing + 1:]).strip()

    if not prompt:
        raise ValueError(
            f"{path}: Markdown body must contain the agent's instructions."
        )

    definition: dict[str, Any] = {
        "description": description,
        "prompt": prompt,
        "tools": tools,
    }

    if "model" in metadata:
        definition["model"] = required_string(metadata, "model", path)

    return name, AgentDefinition(**definition)


def discover_agents(directory: Path) -> dict[str, AgentDefinition]:
    if not directory.is_dir():
        raise ValueError(f"Agent directory does not exist: {directory}")

    files = sorted(directory.glob("*.md"))

    if not files:
        raise ValueError(f"No Markdown agent definitions found in {directory}")

    agents: dict[str, AgentDefinition] = {}
    sources: dict[str, Path] = {}

    for path in files:
        name, definition = load_agent(path)

        if name in agents:
            raise ValueError(
                f"Duplicate agent name '{name}' in "
                f"{sources[name]} and {path}."
            )

        agents[name] = definition
        sources[name] = path

    return agents


async def run(args: argparse.Namespace) -> None:
    root = args.root.resolve()

    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")

    agent_dir = args.agents_dir
    if not agent_dir.is_absolute():
        agent_dir = root / agent_dir

    agents = discover_agents(agent_dir)

    if args.goal_file:
        goal_path = args.goal_file
        if not goal_path.is_absolute():
            goal_path = root / goal_path
        goal = goal_path.read_text(encoding="utf-8").strip()
    else:
        goal = args.goal.strip()

    if not goal:
        raise ValueError("The goal cannot be empty.")

    # Specialists receive their own tool subset from their Markdown files.
    # These tools must also be available in the runtime.
    runtime_tools = sorted(
        set(PARENT_TOOLS).union(
            tool
            for definition in agents.values()
            for tool in (definition.tools or [])
        )
    )

    print(f"[runtime] Project: {root}", flush=True)
    print(
        f"[runtime] Registered agents: {', '.join(agents)}",
        flush=True,
    )
    print(
        "[runtime] File edits are enabled where agent tools permit them; "
        "shell execution is disabled.",
        flush=True,
    )

    from agent_hooks import build_hooks

    options = ClaudeAgentOptions(
        hooks=build_hooks(root, root / "artifacts" / "claude-hooks.jsonl"),
        cwd=str(root),
        system_prompt=ORCHESTRATOR_POLICY,
        agents=agents,
        tools=runtime_tools,
        allowed_tools=runtime_tools,
        permission_mode="acceptEdits",
        setting_sources=["project"],
        strict_mcp_config=True,
        disallowed_tools=["Agent(fork)"],
        max_turns=args.max_turns,
        max_budget_usd=args.budget,
        env={
            "CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS": "1",
            "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1",
            "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": str(args.concurrency),
        },
    )

    delegation_count = 0
    final_result: ResultMessage | None = None

    async for message in query(prompt=goal, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    if block.name in {"Agent", "Task"}:
                        delegation_count += 1
                        target = block.input.get(
                            "subagent_type", "unspecified"
                        )
                        print(f"\n[delegate] {target}", flush=True)

                elif isinstance(block, TextBlock):
                    print(block.text, flush=True)

        elif isinstance(message, ResultMessage):
            final_result = message
            print(f"\n[result] {message.subtype}", flush=True)

            if message.total_cost_usd is not None:
                print(
                    f"[cost] ${message.total_cost_usd:.4f}",
                    flush=True,
                )

    if final_result is None:
        raise RuntimeError("The stream ended without a terminal result.")

    if final_result.is_error:
        raise RuntimeError(
            final_result.result
            or f"Agent run failed: {final_result.subtype}"
        )

    if delegation_count == 0:
        raise RuntimeError(
            "The run ended without observed specialist delegation. "
            "No orchestrated execution has been verified."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coordinate file-defined specialist agents."
    )

    goal = parser.add_mutually_exclusive_group(required=True)
    goal.add_argument("--demo-hooks", action="store_true",
                      help="Exercise local hooks without Claude or API calls.")
    goal.add_argument("--goal", help="Goal for the orchestrator.")
    goal.add_argument(
        "--goal-file",
        type=Path,
        help="Read the goal from a UTF-8 file.",
    )

    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--agents-dir",
        type=Path,
        default=Path(".claude/subagents"),
        help="Agent directory, relative to --root unless absolute.",
    )
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--budget", type=float, default=5.0)
    parser.add_argument("--concurrency", type=int, default=3)

    args = parser.parse_args()

    if args.max_turns < 1:
        parser.error("--max-turns must be at least 1.")
    if args.budget <= 0:
        parser.error("--budget must be greater than 0.")
    if args.concurrency < 1:
        parser.error("--concurrency must be at least 1.")

    return args


def main() -> int:
    try:
        args = parse_args()
        if args.demo_hooks:
            from feature_demo import main as demo
            demo()
        else:
            load_claude_runtime()
            asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"\n[error] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
