#!/usr/bin/env python3
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rich.console import Console

SOURCE = Path(__file__).parents[1] / "pulsedeck.py"
SPEC = importlib.util.spec_from_file_location("pulsedeck", SOURCE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def render_to_text(renderable, width=120):
    console = Console(file=io.StringIO(), width=width)
    console.print(renderable)
    return console.file.getvalue()


def sample_cpu_data():
    return {
        "model": "Test CPU",
        "usage": 10.0,
        "logical_usage": [10.0],
        "cores": [],
        "frequency": None,
        "frequency_max": None,
        "load": (0.0, 0.0, 0.0),
        "package_temperature": None,
        "logical_count": 1,
    }


class IntegratedGpuTests(unittest.TestCase):
    def test_integrated_gpu_requires_nvidia_main(self):
        self.assertIsNone(MODULE.integrated_gpu_data(None))
        self.assertIsNone(MODULE.integrated_gpu_data({"vendor": "Intel", "name": "i"}))

    @patch.object(MODULE, "drm_gpus")
    def test_integrated_gpu_found_beside_discrete(self, drm):
        card = {"vendor": "Intel", "name": "Intel GPU"}
        drm.return_value = [card]
        self.assertEqual(MODULE.integrated_gpu_data({"vendor": "NVIDIA"}), card)

    def test_integrated_usage_prefers_busy_percent(self):
        igpu = {
            "usage": 42.0,
            "frequency_min": 350.0,
            "frequency": 1050.0,
            "frequency_max": 1050.0,
        }
        self.assertEqual(MODULE.integrated_usage(igpu), (42.0, False))

    def test_integrated_usage_estimates_from_clocks(self):
        igpu = {
            "usage": None,
            "frequency_min": 350.0,
            "frequency": 700.0,
            "frequency_max": 1050.0,
        }
        self.assertEqual(MODULE.integrated_usage(igpu), (50.0, True))

    def test_integrated_usage_clamps_and_skips_flat_range(self):
        flat = {"usage": None, "frequency_min": 350.0, "frequency": 350.0, "frequency_max": 350.0}
        self.assertEqual(MODULE.integrated_usage(flat), (None, False))
        above = {
            "usage": None,
            "frequency_min": 350.0,
            "frequency": 2000.0,
            "frequency_max": 1050.0,
        }
        self.assertEqual(MODULE.integrated_usage(above), (100.0, True))

    def test_cpu_panel_hides_igpu_row_without_data(self):
        panel = MODULE.render_cpu({"cpu": sample_cpu_data()}, compact=True)
        self.assertNotIn("IGPU", render_to_text(panel))

    def test_cpu_panel_shows_estimated_igpu_row(self):
        igpu = {
            "vendor": "Intel",
            "name": "Intel GPU (8086:3E9B)",
            "usage": None,
            "frequency_min": 350.0,
            "frequency": 700.0,
            "frequency_max": 1050.0,
        }
        panel = MODULE.render_cpu({"cpu": sample_cpu_data(), "igpu": igpu}, compact=True)
        text = render_to_text(panel)
        self.assertIn("IGPU", text)
        self.assertIn("~50.0%", text)
        self.assertIn("0.70/1.05 GHz", text)


class InterfaceKindTests(unittest.TestCase):
    def test_linux_interface_classification(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, extra in (
                ("wlp0s20f3", "wireless"),
                ("wlp3s0", "phy80211"),
                ("enp8s0", "device"),
                ("vmnet1", None),
            ):
                path = Path(tmp) / name
                path.mkdir()
                if extra:
                    (path / extra).mkdir()
            self.assertEqual(MODULE.interface_kind("wlp0s20f3", tmp), "wifi")
            self.assertEqual(MODULE.interface_kind("wlp3s0", tmp), "wifi")
            self.assertEqual(MODULE.interface_kind("enp8s0", tmp), "ethernet")
            self.assertIsNone(MODULE.interface_kind("vmnet1", tmp))
            self.assertIsNone(MODULE.interface_kind("missing0", tmp))

    @patch.object(MODULE.os, "name", "nt")
    def test_windows_interface_classification(self):
        self.assertEqual(MODULE.interface_kind("Wi-Fi"), "wifi")
        self.assertEqual(MODULE.interface_kind("WLAN 1"), "wifi")
        self.assertEqual(MODULE.interface_kind("Ethernet 2"), "ethernet")
        self.assertIsNone(MODULE.interface_kind("vEthernet (WSL)"))
        self.assertIsNone(MODULE.interface_kind("Loopback Pseudo-Interface"))


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

    @patch.object(
        MODULE.subprocess, "run", side_effect=MODULE.subprocess.TimeoutExpired("nvidia-smi", 2)
    )
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

    def test_output_configuration_detects_legacy_encoding(self):
        with (
            patch.object(MODULE.sys, "stdout", SimpleNamespace(encoding="cp1252")),
            patch.dict(MODULE.os.environ, {}, clear=True),
        ):
            MODULE.configure_output()
            self.assertEqual(MODULE.os.environ["PULSEDECK_ASCII"], "1")

    @patch.object(MODULE, "interface_kind", return_value="ethernet")
    @patch.object(MODULE.time, "monotonic", side_effect=[100.0, 102.0])
    @patch.object(MODULE.psutil, "net_if_stats")
    @patch.object(MODULE.psutil, "net_io_counters")
    def test_network_rates_use_counter_deltas(self, counters, stats, monotonic, kind):
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

    @patch.object(MODULE, "interface_kind", return_value=None)
    @patch.object(MODULE.time, "monotonic", side_effect=[100.0, 102.0])
    @patch.object(MODULE.psutil, "net_if_stats")
    @patch.object(MODULE.psutil, "net_io_counters")
    def test_network_rates_skip_virtual_interfaces(self, counters, stats, monotonic, kind):
        MODULE._network_sample = None
        stats.return_value = {"vmnet1": SimpleNamespace(isup=True)}
        counters.side_effect = [
            {"vmnet1": SimpleNamespace(bytes_sent=100, bytes_recv=200)},
            {"vmnet1": SimpleNamespace(bytes_sent=300, bytes_recv=600)},
        ]
        MODULE.network_data()
        self.assertEqual(MODULE.network_data(), [])

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


class SystemPanelTests(unittest.TestCase):
    def sample_system_data(self):
        return {
            "network": [
                {"name": "wlp0s20f3", "upload": 1.0, "download": 2.0},
                {"name": "enp8s0", "upload": 3.0, "download": 4.0},
            ],
            "disks": [{"mountpoint": "/", "percent": 33.7, "free": 1024}],
        }

    def test_system_panel_never_exceeds_height(self):
        for height in (4, 5, 6, 7, 8, 10, 13):
            panel = MODULE.render_system(self.sample_system_data(), height=height)
            lines = render_to_text(panel, width=60).rstrip("\n").splitlines()
            self.assertLessEqual(len(lines), max(height, 3))

    def test_system_panel_drops_separator_before_entries(self):
        tight = render_to_text(MODULE.render_system(self.sample_system_data(), height=6), width=60)
        self.assertIn("wlp0s20f3", tight)
        self.assertIn("33.7%", tight)

    def test_system_panel_keeps_network_over_disks_when_tiny(self):
        tiny = render_to_text(MODULE.render_system(self.sample_system_data(), height=5), width=60)
        self.assertIn("wlp0s20f3", tiny)
        self.assertNotIn("33.7%", tiny)

    def test_unbounded_render_keeps_all_sections(self):
        full = render_to_text(MODULE.render_system(self.sample_system_data()), width=60)
        self.assertIn("wlp0s20f3", full)
        self.assertIn("enp8s0", full)
        self.assertIn("DISKS", full)

    def test_system_panel_size_caps_content_by_layout_share(self):
        data = self.sample_system_data()
        self.assertEqual(MODULE.system_panel_size(data, 40), 8)
        self.assertEqual(MODULE.system_panel_size(data, 30), 6)
        self.assertEqual(MODULE.system_panel_size({"network": [], "disks": []}, 40), 7)


if __name__ == "__main__":
    unittest.main()
