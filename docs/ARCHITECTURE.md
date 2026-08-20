# PulseDeck Architecture

PulseDeck is intentionally implemented as a small single-file terminal application. It uses standard Linux interfaces plus two Python dependencies.

## Repository Structure

```text
pulsedeck/
├── pulsedeck.py       # collectors, calculations, renderers, live loop
├── monitor.sh         # portable launcher
├── install.sh         # per-user installation and autostart setup
├── requirements.txt   # psutil and rich
├── README.md          # quick-start documentation
└── docs/
    ├── METRICS.md     # metric definitions and formulas
    └── ARCHITECTURE.md
```

## Data Sources

| Data | Source |
| --- | --- |
| CPU model | `/proc/cpuinfo` |
| CPU topology | `/sys/devices/system/cpu/cpu*/topology` |
| CPU usage and frequency | `psutil` |
| Memory and swap | `psutil` |
| Temperatures | `psutil.sensors_temperatures()` |
| Battery | `psutil.sensors_battery()` |
| GPU metrics | `nvidia-smi` |
| Process metrics | `psutil.process_iter()` |

## Refresh Pipeline

Each refresh performs these steps:

1. Read hardware temperatures.
2. Read RAM and swap statistics.
3. Read per-logical-CPU usage and frequency.
4. Map logical CPUs to physical cores.
5. Query NVIDIA metrics with a two-second timeout.
6. Read process metrics.
7. Normalize process CPU values and calculate CPU share.
8. Build a Rich layout based on terminal dimensions.
9. Render the updated screen.

The loop refreshes approximately once per second.

## Main Code Areas

### Collection

- `sensor_data()` reads and preserves temperature labels and limits.
- `gpu_data()` executes `nvidia-smi`, parses CSV output, and converts unsupported numeric values to `None`.
- `cpu_data()` samples CPU usage, reads frequency/load, and creates physical-core rows.
- `process_data()` reads process information, filters dead/zombie processes, normalizes CPU values, and sorts resource users.
- `collect()` combines all values into one snapshot passed to the renderers.

### Normalization

The raw process CPU value is divided by the number of logical CPUs so that the displayed process `CPU` column represents total machine capacity rather than one logical CPU.

The process `SHARE` value is calculated from normalized process CPU divided by total current CPU usage.

### Rendering

- `render_cpu()` displays the CPU model, totals, physical cores, usage, frequency, temperature, and load.
- `render_gpu()` displays NVIDIA metrics and handles unavailable values.
- `render_memory()` displays RAM and swap.
- `render_sensors()` displays readable sensor names and battery state.
- `render_processes()` displays PID, command, CPU, share, RAM percentage, and RSS.
- `build_layout()` selects wide or compact mode based on terminal width and height.

## Layout Modes

Wide mode activates at least 100 columns wide and 28 rows high:

```text
┌──────────────────────┬────────────┐
│ CPU                  │ GPU        │
│                      │ MEMORY     │
│                      │ SENSORS    │
├──────────────────────┴────────────┤
│ TOP RESOURCE USERS                 │
└────────────────────────────────────┘
```

Compact mode removes the detailed thread column, reduces bar widths, and moves sensor details into the footer. This keeps the CPU, GPU, memory, and process panels usable in smaller terminals.

## Startup Installation

`install.sh` calculates the project directory from its own location, so it does not depend on the repository being stored in a particular path.

It performs these actions:

1. Creates the user's local bin and autostart directories.
2. Installs `psutil` and `rich` from `requirements.txt`.
3. Installs the executable as `~/.local/bin/pulsedeck`.
4. Installs the launcher as `~/.local/bin/pulsedeck-monitor.sh`.
5. Creates `pulsedeck.desktop` with the installing user's paths.

The repository's `monitor.sh` is portable and launches the local `pulsedeck.py` beside it. The installed launcher is generated separately so the installed command can be launched from any directory.

## Error Handling

- Missing or failing `nvidia-smi` disables only GPU data.
- Unsupported NVIDIA values become `N/A`.
- Missing temperature sensors produce an empty sensor section instead of crashing.
- Processes that disappear during collection or deny access are skipped.
- Missing frequency information is displayed as unavailable.
- Terminal input is restored when the program exits.

## Testing

Basic checks:

```bash
python3 -m py_compile pulsedeck.py
python3 pulsedeck.py --help
python3 pulsedeck.py --once
bash -n monitor.sh
bash -n install.sh
```

Recommended future automated tests:

- CPU topology grouping
- CPU capacity normalization
- CPU share calculation
- GPU `N/A` parsing
- Memory calculation
- Sensor label mapping
- Compact and wide rendering
- Clean terminal restoration after exit

## Portability Notes

- GPU collection currently supports NVIDIA only.
- Multi-GPU rendering is not implemented; the first `nvidia-smi` row is used.
- Sensor group names differ between hardware vendors and kernel drivers.
- The program is designed for Linux and relies on `/proc`, `/sys`, and Linux sensor APIs.
- The installer uses the current user's local Python environment and does not require root.
