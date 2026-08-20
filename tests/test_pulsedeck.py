import importlib.util
import unittest
from pathlib import Path


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

    def test_byte_formatting(self):
        self.assertEqual(MODULE.bytes_value(1024), "1.0 KiB")
        self.assertEqual(MODULE.bytes_value(1024**2), "1.0 MiB")


if __name__ == "__main__":
    unittest.main()
