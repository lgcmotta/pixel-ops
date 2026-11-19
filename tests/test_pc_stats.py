from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from unittest.mock import patch

from pixel_ops.data_sources.pc_stats import PCStatsSource, _linux_temperature_c, _normalize_disk_path, _parse_tasklist_top_memory, _nvidia_metrics


class PCStatsTests(unittest.TestCase):
    def test_nvidia_temperature_shares_the_single_sample_query(self):
        with patch("pixel_ops.data_sources.pc_stats.shutil.which", return_value="nvidia-smi"), patch("pixel_ops.data_sources.pc_stats._run_command", return_value="Sample GPU, 42, 2048, 16384, 51") as query:
            snapshot = PCStatsSource(fields=["gpu_usage", "vram", "gpu_temperature"]).current()
        query.assert_called_once()
        self.assertEqual(snapshot.metrics[2].numeric_value, 51)
        self.assertEqual(snapshot.metrics[2].unit, "C")

    def test_nvidia_sample_uses_one_query_and_preserves_partial_data(self):
        with patch("pixel_ops.data_sources.pc_stats.shutil.which", return_value="nvidia-smi"), patch("pixel_ops.data_sources.pc_stats._run_command", return_value="Sample GPU, 42, 2048, 16384") as query:
            source = PCStatsSource(fields=["gpu_usage", "vram"])
            snapshot = source.current()
        query.assert_called_once()
        self.assertEqual(snapshot.metrics[0].numeric_value, 42)
        self.assertEqual(snapshot.metrics[1].total, 16384)
        with patch("pixel_ops.data_sources.pc_stats.shutil.which", return_value="nvidia-smi"), patch("pixel_ops.data_sources.pc_stats._run_command", return_value="Sample GPU, [N/A], 2048, 16384"):
            self.assertNotIn("usage", _nvidia_metrics())

    def test_missing_nvidia_tool_is_unknown(self):
        with patch("pixel_ops.data_sources.pc_stats.shutil.which", return_value=None):
            snapshot = PCStatsSource(fields=["gpu_usage", "vram"]).current()
        self.assertTrue(all(metric.status == "unknown" for metric in snapshot.metrics))

    def test_ram_keeps_numeric_bytes_and_total(self):
        from types import SimpleNamespace
        with patch("pixel_ops.data_sources.pc_stats.psutil") as psutil:
            psutil.virtual_memory.return_value = SimpleNamespace(percent=25, used=16 * 1024**3, total=64 * 1024**3)
            metric = PCStatsSource(fields=["ram"]).current().metrics[0]
        self.assertEqual(metric.numeric_value / metric.total, 0.25)
        self.assertEqual(metric.unit, "bytes")

    def test_pc_stats_source_respects_configured_fields(self):
        source = PCStatsSource(fields=["cpu", "ram", "missing_field"], poll_seconds=1)

        snapshot = source.current()

        self.assertIsNotNone(snapshot)
        assert snapshot is not None
        self.assertEqual([metric.key for metric in snapshot.metrics], ["cpu", "ram", "missing_field"])
        self.assertEqual(snapshot.metrics[-1].status, "unknown")

    def test_linux_temperature_reads_sysfs_milli_celsius(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            zone = root / "class/thermal/thermal_zone0"
            zone.mkdir(parents=True)
            (zone / "temp").write_text("45125\n", encoding="utf-8")

            self.assertEqual(_linux_temperature_c(root), 45.125)

    def test_windows_disk_default_uses_system_drive(self):
        with patch("pixel_ops.data_sources.pc_stats.platform.system", return_value="Windows"), patch.dict("os.environ", {"SystemDrive": "D:"}):
            self.assertEqual(_normalize_disk_path("/"), "D:\\")

    def test_windows_tasklist_parser_finds_top_memory_process(self):
        output = '\n'.join(
            [
                '"Code.exe","1234","Console","1","1,234,000 K"',
                '"python.exe","5678","Console","1","98,000 K"',
            ]
        )

        self.assertEqual(_parse_tasklist_top_memory(output), (1_234_000 * 1024, "Code.exe"))


if __name__ == "__main__":
    unittest.main()
