"""Shared edit guard and audit hooks; Claude SDK is optional."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path


class ProjectHooks:
    def __init__(self, root: Path, log_path: Path):
        self.root = root.resolve()
        self.log_path = log_path.resolve()

    def guard(self, file_path):
        if not isinstance(file_path, str) or not file_path:
            return False
        try:
            path = (self.root / file_path).resolve()
            return path.is_relative_to(self.root) and any(
                path.is_relative_to((self.root / name).resolve())
                for name in ('src', 'tests'))
        except (OSError, RuntimeError, ValueError):
            return False

    def audit(self, event, **fields):
        record = dict(timestamp=datetime.now(timezone.utc).isoformat(),
                      event=event, **fields)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record) + '\n')

    def dispatch(self, tool, file_path, text=None):
        """Execute a local file tool, with pre/post/failure hooks around it."""
        self.audit('PreToolUse', tool=tool, file_path=file_path)
        try:
            if tool not in ('Read', 'Write', 'Edit'):
                raise ValueError('Unsupported local tool')
            if tool in ('Write', 'Edit') and not self.guard(file_path):
                raise PermissionError('Edits restricted to src/ and tests/')
            path = (self.root / file_path).resolve()
            if not path.is_relative_to(self.root):
                raise PermissionError('Reads restricted to project')
            if tool == 'Read':
                result = path.read_text(encoding='utf-8')
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
                result = None
        except Exception as exc:
            self.audit('PostToolUseFailure', tool=tool, file_path=file_path,
                       error=type(exc).__name__)
            raise
        self.audit('PostToolUse', tool=tool, file_path=file_path)
        return result


def build_hooks(root: Path, log_path: Path):
    """Adapter for the original optional Claude Agent SDK orchestrator."""
    from claude_agent_sdk import HookMatcher
    hooks = ProjectHooks(root, log_path)
    lock = asyncio.Lock()

    async def guard_edits(data, tool_use_id, context):
        if hooks.guard(data.get('tool_input', {}).get('file_path')):
            return {}
        return {'hookSpecificOutput': {
            'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
            'permissionDecisionReason': 'Edits restricted to src/ and tests/'}}

    async def audit_event(data, tool_use_id, context):
        async with lock:
            hooks.audit(data.get('hook_event_name', 'Unknown'),
                        tool_use_id=tool_use_id, tool=data.get('tool_name'),
                        agent_id=data.get('agent_id'),
                        file_path=data.get('tool_input', {}).get('file_path'))
        return {}

    return {
        'PreToolUse': [HookMatcher(matcher='Write|Edit', hooks=[guard_edits])],
        **{event: [HookMatcher(hooks=[audit_event])] for event in
           ('PostToolUse', 'PostToolUseFailure', 'SubagentStart', 'SubagentStop')},
    }
