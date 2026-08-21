# Changelog

## 0.3.1

- Fix Windows tests when optional temperature APIs are unavailable.
- Fall back to ASCII dashboard bars on legacy Windows console encodings.
- Fix Ruff checks for generated build files and source formatting.

## 0.3.0

- Run GPU collection in a background sampler so delayed NVIDIA tools do not block the dashboard.
- Add cached GPU samples and reduce repeated GPU process probes.
- Add `pyproject.toml` packaging and the `pulsedeck` console command.
- Add Linux and Windows CI checks.

## 0.2.0

- Added Windows support and expanded GPU and system panels.
