# PulseDeck

PulseDeck is a responsive Linux terminal dashboard for CPU, GPU, memory, temperatures, battery status, and running processes.

It combines the useful parts of `nvtop` and `watch sensors` into one terminal interface built with Python, `psutil`, and `rich`.

## Features

- Live dashboard refreshed approximately once per second
- Responsive compact and wide layouts
- CPU usage, frequency, load average, package temperature, physical cores, and logical-thread mapping
- NVIDIA GPU utilization, temperature, VRAM, and power when available
- RAM and swap usage
- NVMe, chipset, Wi-Fi, and battery sensors when exposed by Linux
- Top resource-consuming processes with PID, command, CPU, CPU share, RAM, and RSS
- CPU values normalized against total machine capacity
- Color-coded usage and temperature values
- `q`, `Esc`, and `Ctrl-C` exit controls
- One-shot output with `--once`

## Preview

```text
                         PULSEDECK  //  hostname  //  2026-08-20 09:40:24
╭──────────────────────────── CPU ────────────────────────╮╭──────── GPU ────────╮
│ Intel Core i5-9300H CPU @ 2.40GHz                       ││ GTX 1050   42°C      │
│ TOTAL 21.0%  1.30/4.10 GHz  PACKAGE 48°C  LOAD 1.43     ││ UTIL  0.0%           │
│ Core 0  0,4  ███░░░░░░░  16.4%                    49°C   ││ VRAM  9/3072 MiB      │
╰─────────────────────────────────────────────────────────╯╰──────────────────────╯
```

## Requirements

- Linux
- Python 3.9 or newer recommended
- Python virtual-environment support (`venv`)
- Python packages `psutil` and `rich`
- Optional: NVIDIA, AMD, or Intel GPU drivers/tools for GPU metrics
- Optional: Linux hardware sensors for temperature metrics

On Fedora:

```bash
sudo dnf install python3 python3-psutil python3-rich
```

## Installation

Clone or download this repository, enter the project directory, and run:

```bash
chmod +x install.sh
./install.sh
```

The installer:

- Installs Python dependencies from `requirements.txt`
- Installs the command as `~/.local/bin/pulsedeck`
- Installs a portable launcher
- Creates a KDE/GNOME-compatible autostart entry

The installer does not require root privileges.

## Usage

Run the live dashboard:

```bash
pulsedeck
```

Render one snapshot and exit:

```bash
pulsedeck --once
```

Show help:

```bash
pulsedeck --help
```

Exit the live dashboard with `q`, `Esc`, or `Ctrl-C`.

## CPU Metrics In Brief

- **CPU**: percentage of the complete machine capacity used by a process.
- **SHARE**: percentage of currently active CPU work attributed to a process.
- **TOTAL**: average utilization across all logical CPUs.
- **PACKAGE**: whole-CPU package temperature.
- **LOAD**: one-minute Linux load average, which is different from CPU percentage.

For the complete formulas and examples, see [`docs/METRICS.md`](docs/METRICS.md).

## Documentation

- [`docs/METRICS.md`](docs/METRICS.md): CPU, process, GPU, memory, temperature, and sampling details
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): source structure, data flow, layout behavior, and development notes

## Project Files

```text
pulsedeck/
├── README.md
├── pulsedeck.py
├── monitor.sh
├── install.sh
├── requirements.txt
├── .gitignore
├── tests/
│   └── test_pulsedeck.py
└── docs/
    ├── METRICS.md
    └── ARCHITECTURE.md
```

## Limitations

- GPU metrics use NVIDIA `nvidia-smi` or Linux DRM/sysfs data for AMD and Intel when available.
- Some vendor-specific GPU fields may be unavailable.
- Sensor names vary between machines.
- Process values are interval-based samples, not permanent accounting.
- The process table is read-only.
- No historical graphs are stored.

## Privacy

PulseDeck does not upload or persist monitoring data. Process command lines can contain private paths, usernames, tokens, or other sensitive arguments, so review screenshots before publishing them.

## License

No license has been selected for this prototype yet. Choose and add a license before publishing the project for reuse.
