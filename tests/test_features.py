import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_hooks import ProjectHooks

ROOT = Path(__file__).resolve().parents[1]


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'
        self.root.mkdir()
        self.log = Path(self.tmp.name) / 'events.jsonl'
        self.hooks = ProjectHooks(self.root, self.log)

    def records(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_allowed_write_read_audit(self):
        self.hooks.dispatch('Write', 'src/example.py', 'hello\n')
        self.assertEqual(self.hooks.dispatch('Read', 'src/example.py'), 'hello\n')
        self.assertEqual([r['event'] for r in self.records()],
                         ['PreToolUse', 'PostToolUse'] * 2)

    def test_denied_write_preserves_protected_file(self):
        target = self.root / 'README.md'
        target.write_text('preserved')
        with self.assertRaises(PermissionError):
            self.hooks.dispatch('Write', 'README.md', 'overwrite')
        self.assertEqual(target.read_text(), 'preserved')
        self.assertEqual(self.records()[-1]['event'], 'PostToolUseFailure')

    def test_traversal_and_missing_path_rejected(self):
        for path in (None, '', '../outside.py', 'src/../../outside.py',
                     'src/../README.md', 'src-other/example.py'):
            with self.subTest(path=path):
                self.assertFalse(self.hooks.guard(path))
                with self.assertRaises(PermissionError):
                    self.hooks.dispatch('Write', path, 'bad')

    def test_symlink_escape_rejected(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (self.root / 'src').mkdir()
        (self.root / 'src' / 'link').symlink_to(outside, target_is_directory=True)
        self.assertFalse(self.hooks.guard('src/link/escape.py'))
        with self.assertRaises(PermissionError):
            self.hooks.dispatch('Write', 'src/link/escape.py', 'bad')
        self.assertFalse((outside / 'escape.py').exists())

    def test_symlinked_allowed_root_rejected(self):
        outside = Path(self.tmp.name) / 'outside'
        outside.mkdir()
        (self.root / 'src').symlink_to(outside, target_is_directory=True)
        self.assertFalse(self.hooks.guard('src/escape.py'))
        with self.assertRaises(PermissionError):
            self.hooks.dispatch('Write', 'src/escape.py', 'bad')
        self.assertFalse((outside / 'escape.py').exists())

    def test_missing_read_audited(self):
        with self.assertRaises(FileNotFoundError):
            self.hooks.dispatch('Read', 'missing.py')
        self.assertEqual(self.records()[-1]['error'], 'FileNotFoundError')

    def test_orchestrator_local_demo_without_optional_dependencies(self):
        result = subprocess.run([sys.executable, 'orchestrator.py', '--demo-hooks'],
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('POST hooks audited', result.stdout)

    def test_demo_integration(self):
        readme = (ROOT / 'README.md').read_bytes()
        result = subprocess.run([sys.executable, 'feature_demo.py'], cwd=ROOT,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('blocked protected README.md write', result.stdout)
        self.assertEqual((ROOT / 'README.md').read_bytes(), readme)
