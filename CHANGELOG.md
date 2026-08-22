# Changelog

## 0.5.0

- Measure integrated GPU utilization from `/proc/*/fdinfo` engine-time deltas on drivers without a busy-percent file, falling back to the clock-based estimate only until the first delta exists.
- Block on the GPU sampler in `--once` mode so single-shot renders include GPU and integrated GPU data.
- Add live battery discharge wattage to the SENSORS panel and compact footer.
- Add a `GPU` activity column to the TOP RESOURCE USERS table on systems with `nvidia-smi`.
- Keep every compact-mode panel visible on short terminals by shrinking the GPU panel and its `APPS` list first.
- Apply `ruff` formatting across the source and gate formatting in CI.
- Fix fdinfo path resolution so integrated engine scanning actually reads client counters.
- Fix Windows-only test failures in battery wattage and integrated GPU probes.

## 0.4.0

- Show integrated GPU consumption in the CPU panel on hybrid NVIDIA systems, estimated from Intel clock counters when the driver has no busy-percent file.
- List only Wi-Fi and Ethernet adapters in the system panel; bridges, tunnels, VPN links, and hypervisor networks are filtered out.
- Size the SYSTEM panel to its content and trim interface/disk rows on short terminals so the panel always fits without cropping.

## 0.3.1

- Fix Windows tests when optional temperature APIs are unavailable.
- Fall back to ASCII dashboard bars on legacy Windows console encodings.
- Fix Ruff checks for generated build files and source formatting.
- Improve Linux and Windows installation instructions and align the documentation with the implemented metrics and platform behavior.

## 0.3.0

- Run GPU collection in a background sampler so delayed NVIDIA tools do not block the dashboard.
- Add cached GPU samples and reduce repeated GPU process probes.
- Add `pyproject.toml` packaging and the `pulsedeck` console command.
- Add Linux and Windows CI checks.

## 0.2.0

- Added Windows support and expanded GPU and system panels.
