"""Exercise real shared hooks without an SDK, model call, or project edits."""
import tempfile
from pathlib import Path
from agent_hooks import ProjectHooks


def main():
    root = Path(__file__).resolve().parent
    hooks = ProjectHooks(root, root / 'artifacts' / 'hooks.jsonl')
    skill = hooks.dispatch('Read', '.claude/skills/verification_report/SKILL.md')
    assert 'verification-report' in skill
    print('Read verification-report skill through audited file tool.')
    try:
        hooks.dispatch('Write', 'README.md', 'This must never be written')
    except PermissionError:
        print('PRE hook blocked protected README.md write; failure audited.')
    else:
        raise AssertionError('Protected write was permitted')
    # Exercise the allowed branch in isolation; no source files are modified.
    with tempfile.TemporaryDirectory() as directory:
        sandbox = ProjectHooks(Path(directory), hooks.log_path)
        sandbox.dispatch('Write', 'src/probe.py', '# hook probe\n')
        assert sandbox.dispatch('Read', 'src/probe.py') == '# hook probe\n'
    print('Allowed temporary src/ write and read completed; POST hooks audited.')
    print('Audit log: artifacts/hooks.jsonl (appends real events).')
    print('This is a hook demonstration, not a simulated AI sub-agent run.')


if __name__ == '__main__':
    main()
