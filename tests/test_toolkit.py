"""The unified entry point must preserve the existing approval boundary."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('toolkit_entry', ROOT / 'scripts/a365-toolkit.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class ToolkitTests(unittest.TestCase):
    def test_offline_commands_never_spawn_executors(self):
        with patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
            for args in ([], ['capabilities'], ['workflow'], ['purview']):
                self.assertEqual(entry.main(args), 0)
            run.assert_not_called()

    def test_arguments_and_exit_codes_are_preserved_without_implied_approval(self):
        for service, script in [('tenant', 'a365.py'), ('sentinel', 'a365-admin.py')]:
            with patch.object(entry.subprocess, 'run') as run:
                run.return_value.returncode = 2
                self.assertEqual(entry.main([service, 'apply', '--plan-file', 'reviewed.json']), 2)
                self.assertEqual(run.call_args.args[0], [sys.executable, str(ROOT / 'scripts' / script), 'apply', '--plan-file', 'reviewed.json'])
                self.assertFalse(run.call_args.kwargs.get('shell', False))

    def test_unknown_command_does_not_spawn(self):
        with patch.object(entry.subprocess, 'run') as run, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(entry.main(['execute-everything']), 1)
            self.assertEqual(entry.main(['workflow', '--execute']), 1)
            run.assert_not_called()
