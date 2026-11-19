from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from pixel_ops.data_sources.codex_account import resolve_executable


def test_boot_path_can_find_the_installed_native_codex_without_injected_path():
    with TemporaryDirectory() as directory:
        executable = Path(directory) / 'OpenAI/Codex/bin/version/codex.exe'
        executable.parent.mkdir(parents=True)
        executable.touch()
        with patch('pixel_ops.data_sources.codex_account.sys.platform', 'win32'), patch.dict('os.environ', {'LOCALAPPDATA': directory}), patch('pixel_ops.data_sources.codex_account.shutil.which', return_value=None):
            assert resolve_executable() == str(executable)
            with pytest.raises(FileNotFoundError):
                resolve_executable('my-custom-codex.exe')
