from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from claude_agent_sdk import HookMatcher


def build_hooks(root: Path, log_path: Path):
    root = root.resolve()
    log_path = log_path.resolve()
    lock = asyncio.Lock()

    # Application policy: agents may edit implementation and tests,
    # but not their instructions, runtime, or audit records.
    writable_roots = (
        (root / "src").resolve(),
        (root / "tests").resolve(),
    )

    def deny(reason: str) -> dict:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }

    async def guard_edits(input_data, tool_use_id, context):
        try:
            tool_input = input_data.get("tool_input", {})
            raw_path = tool_input.get("file_path")

            if not isinstance(raw_path, str) or not raw_path:
                return deny("A valid file_path is required.")

            path = Path(raw_path)

            if not path.is_absolute():
                path = root / path

            path = path.resolve()

            if not any(path.is_relative_to(base) for base in writable_roots):
                return deny(
                    "Edits are restricted to src/ and tests/. "
                    "Runtime, configuration, and other files are protected."
                )

            return {}

        except Exception:
            # Fail closed for policy evaluation errors.
            return deny("Unable to validate the requested edit path.")

    async def audit_event(input_data, tool_use_id, context):
        tool_input = input_data.get("tool_input", {})

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": input_data["hook_event_name"],
            "session_id": input_data.get("session_id"),
            "agent_id": input_data.get("agent_id"),
            "agent_type": input_data.get("agent_type"),
            "tool_use_id": tool_use_id,
            "tool_name": input_data.get("tool_name"),
            "file_path": tool_input.get("file_path"),
        }

        async with lock:
            log_path.parent.mkdir(parents=True, exist_ok=True)

            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")

        return {}

    return {
        "PreToolUse": [
            HookMatcher(
                matcher="Write|Edit",
                hooks=[guard_edits],
                on_failure="block",
            ),
        ],
        "PostToolUse": [
            HookMatcher(hooks=[audit_event]),
        ],
        "PostToolUseFailure": [
            HookMatcher(hooks=[audit_event]),
        ],
        "SubagentStart": [
            HookMatcher(hooks=[audit_event]),
        ],
        "SubagentStop": [
            HookMatcher(hooks=[audit_event]),
        ],
    }
