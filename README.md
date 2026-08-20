# PulseDeck

PulseDeck is a live Linux terminal dashboard for CPU, GPU, memory, temperatures, battery status, and running processes.

It combines the useful parts of `nvtop` and `watch sensors` into one responsive terminal interface built with Python, `psutil`, and `rich`.

## Preview

```text
                         PULSEDECK  //  hostname  //  2026-08-20 09:40:24
╭──────────────────────────── CPU ────────────────────────╮╭──────── GPU ────────╮
│ Intel Core i5-9300H CPU @ 2.40GHz                       ││ GTX 1050   42°C      │
│ TOTAL 21.0%  1.30/4.10 GHz  PACKAGE 48°C  LOAD 1.43     ││ UTIL  0.0%           │
│ Core 0  0,4  ███░░░░░░░  16.4%                    49°C   ││ VRAM  9/3072 MiB      │
│ Core 1  1,5  ██░░░░░░░  16.7%                    46°C   │╰──────────────────────╯
╰─────────────────────────────────────────────────────────╯╭──── MEMORY ─────────╮
                                                          │ RAM 4.5/7.6 GiB      │
╭──────────────────── TOP RESOURCE USERS ────────────────╯│ SWAP 128 MiB/7.6 GiB │
│ PID   COMMAND                 CPU    SHARE    RSS       ╰──────────────────────╯
│ 3877  pulsedeck               9.0%   43.1%    28 MiB    │
│ 3180  sunshine                3.9%   18.5%   344 MiB    │
╰─────────────────────────────────────────────────────────╯
```

The exact layout changes with terminal size.

## Features

- Live dashboard refreshed approximately once per second
- Compact layout for small terminals and detailed layout for wide terminals
- CPU model, total usage, current/max frequency, package temperature, and load average
- Physical-core usage with correct logical-thread mapping
- NVIDIA GPU temperature, utilization, VRAM, and power when available
- RAM and swap usage
- NVMe, chipset, Wi-Fi, and battery readings when exposed by Linux
- Top resource-consuming processes with PID and command
- Process CPU normalized against the complete machine capacity
- Separate process CPU share showing responsibility for current CPU work
- Color-coded utilization and temperature values
- `q`, `Esc`, and `Ctrl-C` exit controls
- `--once` mode for one-shot output and testing
- No root privileges required
- No monitoring data is uploaded or saved

## Requirements

Required:

- Linux
- Python 3.9 or newer recommended
- Python packages `psutil` and `rich`

Optional:

- NVIDIA driver and `nvidia-smi` for GPU information
- Linux hardware sensors for temperature information
- Battery support exposed through `/sys` or ACPI

### Fedora

```bash
sudo dnf install python3 python3-psutil python3-rich
```

### Other distributions

Install the equivalent packages using the distribution package manager. If distribution packages are unavailable, use a virtual environment rather than installing application dependencies globally:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install psutil rich
```

## Running

Install PulseDeck for the current user, including its Python dependencies and KDE autostart entry:

```bash
chmod +x install.sh
./install.sh
```

The installer places the command in `~/.local/bin/pulsedeck` and creates `pulsedeck.desktop` under the user's autostart directory. It does not require root privileges.

Run the live dashboard:

```bash
python3 pulsedeck.py
```

If the executable is installed in `~/.local/bin` and that directory is in `PATH`:

```bash
pulsedeck
```

Render a single snapshot:

```bash
pulsedeck --once
```

Show help:

```bash
pulsedeck --help
```

Exit the live dashboard with:

```text
q
Esc
Ctrl-C
```

## Understanding The CPU Panel

Example:

```text
TOTAL  21.0%   1.30/4.10 GHz   PACKAGE 48°C   LOAD 1.43
 CORE    THREADS    USAGE                                      TEMP
 Core 0  0,4        ██░░░░░░░░░░░░  16.4%                      49°C
```

### Total CPU

`TOTAL` is the average utilization across all logical CPUs. On an eight-thread CPU, four fully active threads and four idle threads produce approximately 50% total usage.

The implementation obtains per-logical-CPU usage from `psutil` and averages the values:

```python
logical_usage = psutil.cpu_percent(interval=None, percpu=True)
total_usage = sum(logical_usage) / len(logical_usage)
```

### Frequency

`1.30/4.10 GHz` means:

- Current reported frequency: 1.30 GHz
- Maximum reported frequency: 4.10 GHz

Frequency changes with workload, power management, Turbo Boost, and thermal conditions.

### Package temperature

`PACKAGE` is the temperature reported for the whole CPU package by the Linux `coretemp` sensor. It is not the temperature of one individual core.

### Load average

`LOAD` is the one-minute Linux load average. It represents runnable or waiting work and is not equivalent to CPU utilization. A high load can include processes waiting on disk or other resources.

### Physical cores and logical threads

PulseDeck reads CPU topology from:

```text
/sys/devices/system/cpu/cpu*/topology/physical_package_id
/sys/devices/system/cpu/cpu*/topology/core_id
```

For a typical four-core/eight-thread CPU:

```text
Physical Core 0 -> logical CPUs 0 and 4
Physical Core 1 -> logical CPUs 1 and 5
Physical Core 2 -> logical CPUs 2 and 6
Physical Core 3 -> logical CPUs 3 and 7
```

The displayed physical-core usage is the average of that core's logical threads. Core temperatures are matched using labels such as `Core 0`, not by assuming sensor order.

## Understanding Process CPU Percentages

The process table has two CPU columns:

```text
CPU       SHARE
```

### CPU: percentage of complete machine capacity

Operating-system process APIs commonly report 100% when a process fully occupies one logical CPU. On an eight-logical-CPU system, that is only 12.5% of the complete machine capacity.

PulseDeck normalizes the raw process value:

```python
cpu_capacity = raw_cpu_percent / logical_cpu_count
```

Example:

```text
Raw process value:       100%
Logical CPU count:         8
PulseDeck CPU value:      12.5%
```

Therefore, the `CPU` column answers:

> What percentage of the entire CPU capacity is this process using?

### SHARE: percentage of current CPU work

`SHARE` compares a process with the current total CPU usage:

```python
cpu_share = process_cpu_capacity / total_cpu_usage * 100
```

Example:

```text
Total CPU usage:       21%
Process CPU capacity:   9%
Process SHARE:         42.9%
```

This means the process accounts for approximately 42.9% of the CPU work observed in that sample. It does **not** mean the entire CPU is 42.9% busy.

`SHARE` can be high when total CPU usage is low. That is expected when one process is responsible for most of the small amount of active work. `CPU` is the value to use when deciding whether the whole machine is heavily loaded.

The top rows do not necessarily add up to 100% `SHARE`, because PulseDeck displays only the top processes and some processes may be inaccessible.

## GPU Metrics

GPU data comes from:

```bash
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits
```

The dashboard displays:

- GPU name
- GPU temperature
- GPU utilization
- Used and total VRAM
- Power draw when supported

Unsupported values are shown as `N/A`. For example, some laptop GPUs do not expose power draw through `nvidia-smi`. PulseDeck does not display an unavailable value as `0 W` because that would be misleading.

If `nvidia-smi` is missing or fails, the dashboard shows `NVIDIA data unavailable` while CPU and system metrics continue working.

## Memory Metrics

RAM usage is calculated as:

```python
memory_used = memory.total - memory.available
```

The panel displays:

- RAM used and total
- RAM usage bar
- Swap used and total
- Swap usage bar

`RSS` in the process table means resident set size: memory from that process currently resident in physical RAM. RSS values from multiple processes should not be added as an exact total because shared memory can appear in more than one process.

## Temperature Sensors

PulseDeck reads `psutil.sensors_temperatures()`. Common Linux sensor groups are mapped to readable labels:

| Linux sensor group | Display label |
| --- | --- |
| `coretemp` | CPU package and physical-core temperatures |
| `nvme` | NVMe 1, NVMe 2, and so on |
| `pch_*` | Chipset |
| `iwlwifi_*` | Wi-Fi |
| Other groups | Converted sensor group name |

When a sensor provides a critical limit, PulseDeck uses it. Otherwise, it uses a 90°C fallback for general sensors. Temperature colors are:

- Green: below 80% of the critical limit
- Yellow: at least 80% of the critical limit
- Red: at least 90% of the critical limit

## Architecture

The program is intentionally a single-file terminal application.

```text
pulsedeck.py
├── system collectors
│   ├── /proc/cpuinfo
│   ├── /sys/devices/system/cpu
│   ├── psutil CPU and memory APIs
│   ├── psutil temperature APIs
│   └── nvidia-smi subprocess
├── normalization
│   ├── physical-core mapping
│   ├── process CPU normalization
│   └── process CPU share calculation
├── renderers
│   ├── CPU panel
│   ├── GPU panel
│   ├── memory panel
│   ├── sensors panel
│   └── process table
└── Rich live terminal loop
```

Each refresh follows this flow:

1. Read temperatures.
2. Read memory and swap.
3. Read per-logical-CPU usage and frequency.
4. Map logical CPUs to physical cores.
5. Query NVIDIA data with a two-second timeout.
6. Read process metrics.
7. Normalize process CPU values.
8. Build the layout for the terminal size.
9. Refresh the screen.

The normal refresh interval is configured by:

```python
REFRESH_SECONDS = 1.0
```

## Terminal Layout

### Wide mode

Wide mode is enabled at least 100 columns wide and 28 rows high. It displays CPU on the left, GPU/memory/sensors on the right, and processes across the bottom.

### Compact mode

Compact mode is used for smaller terminals. It removes the detailed thread column, reduces bar widths, and moves sensor values into the footer so the most important metrics remain visible.

## Autostart Example

The current local setup launches PulseDeck through KDE autostart:

```text
KDE login
  -> ~/.config/autostart/pulsedeck.desktop
  -> konsole -e ~/.local/bin/monitor.sh
  -> exec ~/.local/bin/pulsedeck
```

Example wrapper:

```bash
#!/usr/bin/env bash
exec "$HOME/.local/bin/pulsedeck"
```

Example desktop entry:

```ini
[Desktop Entry]
Type=Application
Name=PulseDeck System Monitor
Exec=konsole -e /home/USER/.local/bin/monitor.sh
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
```

For a public project, do not hard-code a specific username. Use an installer that substitutes `$HOME` or creates the desktop entry for the installing user.

## Testing

Basic validation:

```bash
python3 -m py_compile pulsedeck.py
python3 pulsedeck.py --help
python3 pulsedeck.py --once
```

Validate a desktop entry:

```bash
desktop-file-validate ~/.config/autostart/pulsedeck.desktop
```

Recommended automated tests:

- CPU topology maps logical CPUs to physical cores
- Total CPU is the average of per-logical-CPU values
- Process CPU is divided by logical CPU count
- Process share is based on total current CPU usage
- GPU `N/A` values remain unavailable instead of becoming zero
- Memory used equals total minus available
- Compact and wide layouts render without exceptions
- `q` and `Esc` exit cleanly

## Suggested Repository Layout

```text
pulsedeck/
├── README.md
├── LICENSE
├── pyproject.toml
├── pulsedeck.py
├── monitor.sh
├── install.sh
├── requirements.txt
├── .gitignore
└── tests/
    └── test_pulsedeck.py
```

Before publishing, move the current local script into `src/pulsedeck.py`, add package metadata, create an installer, replace absolute paths, and add tests. The current user-local installation is a working prototype rather than a fully packaged Python project.

## Limitations

- GPU support currently targets NVIDIA through `nvidia-smi`.
- Only the first GPU returned by `nvidia-smi` is rendered.
- Sensor names vary between machines.
- Process values are interval-based samples, not permanent accounting.
- The process table is read-only and cannot kill or reprioritize processes.
- No historical graphs are stored.
- Some process details may be unavailable without elevated permissions.
- The current autostart paths are machine-specific and should be made portable before publishing.

## Privacy And Security

- PulseDeck runs as the current user.
- It does not upload or persist monitoring data.
- It invokes the local `nvidia-smi` executable only.
- Process command lines can contain usernames, private paths, tokens, or other sensitive arguments. Review screenshots before publishing them.
- Hardware names and sensor values can identify a machine model.

## License

No license has been selected for the current prototype. Choose a license before publishing. MIT is a common option for a small utility, but the project owner should choose the license intentionally.
