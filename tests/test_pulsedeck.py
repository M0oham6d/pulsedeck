#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SOURCE = Path(__file__).parents[1] / "pulsedeck.py"
SPEC = importlib.util.spec_from_file_location("pulsedeck", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PulseDeckTests(unittest.TestCase):
    def test_process_cpu_is_normalized_to_machine_capacity(self):
        capacity, share = MODULE.normalize_process_cpu(100.0, 8, 20.0)
        self.assertEqual(capacity, 12.5)
        self.assertEqual(share, 62.5)

    def test_process_share_is_zero_when_cpu_is_idle(self):
        capacity, share = MODULE.normalize_process_cpu(100.0, 8, 0.0)
        self.assertEqual(capacity, 12.5)
        self.assertEqual(share, 0.0)

    def test_unavailable_gpu_values_are_none(self):
        self.assertIsNone(MODULE.number_or_none("N/A"))
        self.assertIsNone(MODULE.number_or_none("[N/A]"))
        self.assertEqual(MODULE.number_or_none("42.5"), 42.5)

    @patch.object(MODULE.subprocess, "run", side_effect=MODULE.subprocess.TimeoutExpired("nvidia-smi", 2))
    def test_nvidia_gpu_timeout_is_treated_as_unavailable(self, run):
        self.assertIsNone(MODULE.nvidia_gpu_data())

    @patch.object(MODULE.psutil, "sensors_temperatures", side_effect=OSError, create=True)
    def test_sensor_failure_returns_empty_data(self, sensors_temperatures):
        self.assertEqual(MODULE.sensor_data(), {})

    @patch.object(MODULE.subprocess, "run")
    def test_nvidia_gpu_processes_parse_graphics_clients(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = (
            "# gpu         pid   type     sm    mem    enc    dec    jpg    ofa    command\n"
            "    0       2075   C+G      -      -      -      0      -      -    kwin_wayland\n"
            "    0      67182   C+G     10      5     16      -      -      -    obs\n"
        )
        self.assertEqual(
            MODULE.nvidia_gpu_processes(),
            [
                {
                    "gpu": "0",
                    "pid": 2075,
                    "type": "C+G",
                    "sm": None,
                    "memory": None,
                    "encoder": None,
                    "decoder": 0.0,
                    "command": "kwin_wayland",
                },
                {
                    "gpu": "0",
                    "pid": 67182,
                    "type": "C+G",
                    "sm": 10.0,
                    "memory": 5.0,
                    "encoder": 16.0,
                    "decoder": None,
                    "command": "obs",
                },
            ],
        )

    def test_byte_formatting(self):
        self.assertEqual(MODULE.bytes_value(1024), "1.0 KiB")
        self.assertEqual(MODULE.bytes_value(1024**2), "1.0 MiB")

    @patch.object(MODULE.time, "monotonic", side_effect=[100.0, 102.0])
    @patch.object(MODULE.psutil, "net_if_stats")
    @patch.object(MODULE.psutil, "net_io_counters")
    def test_network_rates_use_counter_deltas(self, counters, stats, monotonic):
        MODULE._network_sample = None
        stats.return_value = {
            "eth0": SimpleNamespace(isup=True),
            "lo": SimpleNamespace(isup=True),
        }
        counters.side_effect = [
            {"eth0": SimpleNamespace(bytes_sent=100, bytes_recv=200)},
            {"eth0": SimpleNamespace(bytes_sent=300, bytes_recv=600)},
        ]
        MODULE.network_data()
        self.assertEqual(
            MODULE.network_data(),
            [{"name": "eth0", "upload": 100.0, "download": 200.0}],
        )

    @patch.object(MODULE.psutil, "disk_usage")
    @patch.object(MODULE.psutil, "disk_partitions")
    def test_disk_data_reports_mount_usage(self, partitions, usage):
        partitions.return_value = [
            SimpleNamespace(mountpoint="/"),
            SimpleNamespace(mountpoint="/home"),
        ]
        usage.return_value = SimpleNamespace(percent=25.0, used=256, total=1024, free=768)
        self.assertEqual(
            MODULE.disk_data(),
            [{"mountpoint": "/", "percent": 25.0, "used": 256, "total": 1024, "free": 768}],
        )


if __name__ == "__main__":
    unittest.main()
