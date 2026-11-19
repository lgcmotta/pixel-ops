from contextlib import nullcontext
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

import psutil

from pixel_ops.desktop import DesktopManager


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.manager = DesktopManager(Path(self.directory.name))
        self.manager.lock = lambda *args, **kwargs: nullcontext()

    def test_process_identity_rejects_reused_pid(self):
        self.manager._path('display').write_text(json.dumps({'pid': 123, 'created_at': 1}))
        reused = MagicMock()
        reused.create_time.return_value = 2
        with patch('pixel_ops.desktop.psutil.Process', return_value=reused), patch('pixel_ops.desktop.psutil.process_iter', return_value=[]):
            self.assertIsNone(self.manager.process('display'))
        reused.terminate.assert_not_called()

    def test_other_repository_process_cannot_be_adopted(self):
        process = MagicMock()
        process.cmdline.return_value = ['python', 'pixel_ops/main.py']
        process.cwd.return_value = str(self.manager.root.parent)
        self.assertFalse(self.manager._matches(process, 'display'))
        process.cwd.return_value = str(self.manager.root)
        self.assertTrue(self.manager._matches(process, 'display'))

    def test_repeated_start_reuses_process(self):
        process = MagicMock()
        with patch.object(self.manager, 'process', return_value=process), patch.object(self.manager, '_record', return_value=process), patch.object(self.manager, '_spawn') as spawn:
            self.assertIs(self.manager.start('studio'), process)
        spawn.assert_not_called()

    def test_stopping_studio_preserves_display_and_its_account_worker(self):
        studio, display, account, bundler = [MagicMock() for _ in range(4)]
        studio.pid, display.pid, account.pid, bundler.pid = 10, 20, 30, 40
        studio.children.return_value = [display, account, bundler]
        display.children.return_value = [account]
        with patch.object(self.manager, 'process', side_effect=lambda kind: studio if kind == 'studio' else display), patch('pixel_ops.desktop.psutil.wait_procs', return_value=([], [])):
            self.manager.stop('studio')
        studio.terminate.assert_called_once()
        bundler.terminate.assert_called_once()
        display.terminate.assert_not_called()
        account.terminate.assert_not_called()

    def test_stop_ignores_already_closed_process(self):
        with patch.object(self.manager, 'process', return_value=None), patch('pixel_ops.desktop.psutil.wait_procs') as wait:
            self.manager.stop('studio')
        wait.assert_not_called()
