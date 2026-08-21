# PulseDeck

PulseDeck is a responsive Linux and Windows terminal dashboard for CPU, GPU, memory, temperatures, battery status, and running processes.

It combines the useful parts of `nvtop` and `watch sensors` into one terminal interface built with Python, `psutil`, and `rich`.

## Features

- Live dashboard refreshed approximately once per second
- Responsive compact and wide layouts
- CPU usage, frequency, load average, package temperature, physical cores, and logical-thread mapping
- NVIDIA GPU utilization, temperature, VRAM, and power when available
- AMD and Intel GPU detection through Linux DRM/sysfs when available
- RAM and swap usage
- Active network interfaces with upload/download rates
- Filesystem disk usage and free space
- NVMe, chipset, Wi-Fi, CPU, and battery sensors when exposed by the operating system
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

## Supported Platforms

- Linux distributions with Python 3, `psutil`, and `rich`
- Windows 10 and Windows 11 with Python 3

Linux exposes more hardware sensors and GPU interfaces, so Linux generally provides more complete metrics. Windows still supports the platform-neutral CPU, memory, process, battery, and optional NVIDIA metrics.

## Requirements

- Linux or Windows
- Python 3.9 or newer recommended
- Python virtual-environment support (`venv`)
- Python packages `psutil` and `rich`
- Optional: NVIDIA, AMD, or Intel GPU drivers/tools for GPU metrics
- Optional: Linux hardware sensors for temperature metrics

On Fedora:

```bash
sudo dnf install python3 python3-psutil python3-rich
```

## Linux Installation

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

Set `PULSEDECK_BIN_DIR` to choose a different per-user executable directory. The default is
`~/.local/bin`; application data and the virtual environment remain under `XDG_DATA_HOME`.

## Windows Installation

PulseDeck supports Windows 10 and Windows 11 with Python 3.9 or newer.

Install Python from <https://www.python.org/downloads/windows/> and enable **Add Python to PATH** during installation.

Open PowerShell in the project directory and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

The Windows installer:

- Creates a private virtual environment under `%LOCALAPPDATA%\PulseDeck\venv`
- Installs `psutil` and `rich`
- Installs PulseDeck under `%LOCALAPPDATA%\PulseDeck`
- Creates `pulsedeck.cmd`
- Adds the installation directory to the current user's PATH

Open a new PowerShell window after installation and run:

```powershell
pulsedeck
```

One snapshot:

```powershell
pulsedeck --once
```

To run directly from the repository instead:

```powershell
py -3 -m pip install -r requirements.txt
py -3 .\pulsedeck.py
```

Windows uses `psutil` for CPU, frequency, memory, swap/page-file, process, and battery metrics. NVIDIA GPU metrics are available when `nvidia-smi.exe` is installed and available in `PATH`:

```powershell
nvidia-smi
```

The following Linux-specific features may show `N/A` on Windows:

- `/proc` CPU details
- `/sys` CPU topology details
- Linux hardware temperature sensors
- AMD and Intel Linux DRM/sysfs GPU metrics
- CPU package and per-core temperatures
- KDE/Konsole autostart

The dashboard continues running when these values are unavailable. Windows keyboard input uses `msvcrt`, while Linux uses terminal input support through `termios`.

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
- **LOAD**: one-minute system load average when the platform provides it; it is different from CPU percentage.

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
├── pyproject.toml
├── .gitignore
├── install_windows.ps1
├── run_windows.ps1
├── tests/
│   └── test_pulsedeck.py
└── docs/
    ├── METRICS.md
    └── ARCHITECTURE.md
```

The current release version is `0.3.0`. See [`CHANGELOG.md`](CHANGELOG.md) for release notes.


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

PulseDeck is licensed under the MIT License.

See the [LICENSE](LICENSE) file for the complete license text.
