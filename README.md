# PulseDeck

PulseDeck is a cross-platform terminal dashboard for CPU, GPU, memory, temperatures, battery status, networking, disk space, and running processes. It is a small Python application built with `psutil` and `rich`.

## What It Shows

- Live readings refreshed approximately every second
- Compact and wide layouts selected from the terminal size
- CPU utilization, current/max frequency, one-minute load, package temperature, physical-core rows, and logical-thread mapping where the operating system exposes it
- NVIDIA utilization, temperature, VRAM, power draw, and active GPU applications when `nvidia-smi` is available
- AMD and Intel GPU data through Linux DRM/sysfs when available
- RAM and swap usage
- Up to four active network interfaces with upload/download rates
- The operating system root filesystem's usage and free space
- Available NVMe, chipset, Wi-Fi, CPU, and battery sensor readings
- Top 16 processes sorted by normalized CPU usage, with PID, command, CPU, CPU share, RAM percentage, and RSS
- Color-coded usage and temperature values

Missing drivers, sensors, permissions, or platform APIs are shown as unavailable where possible; they do not disable the rest of the dashboard.

## Requirements

- Linux or Windows 10/11
- Python 3.9 or newer
- Python's `venv` module for the installer
- A terminal emulator
- Internet access during installation, so Python packages can be installed

The required Python packages are installed automatically:

- `psutil >= 5.9, < 7`
- `rich >= 13.0, < 15`

Optional hardware integrations do not need to be installed for the CPU, memory, process, and basic system panels:

- NVIDIA GPU metrics require `nvidia-smi` (`nvidia-smi.exe` on Windows) in `PATH`
- AMD and Intel GPU metrics are Linux-only and use DRM/sysfs files exposed by the kernel
- Temperature readings depend on what the operating system and hardware drivers expose

## Install On Linux

From a shell, clone the repository and enter it:

```bash
git clone https://github.com/M0oham6d/pulsedeck.git
cd pulsedeck
```

Run the per-user installer:

```bash
chmod +x install.sh
./install.sh
```

The installer does not require `sudo`. It:

1. Creates a private virtual environment under `${XDG_DATA_HOME:-~/.local/share}/pulsedeck/venv`.
2. Installs PulseDeck and its dependencies from `pyproject.toml`.
3. Creates a launcher at `~/.local/bin/pulsedeck`.
4. Creates a desktop autostart entry only if `konsole` is installed.

Run the command from a new shell:

```bash
pulsedeck
```

If the shell says `pulsedeck: command not found`, add the default executable directory to your current `PATH` and retry:

```bash
export PATH="$HOME/.local/bin:$PATH"
pulsedeck
```

To install the launcher somewhere else, set `PULSEDECK_BIN_DIR` before running the installer:

```bash
PULSEDECK_BIN_DIR="$HOME/bin" ./install.sh
```

The virtual environment and application data remain under `${XDG_DATA_HOME:-~/.local/share}/pulsedeck` regardless of the launcher directory. Set `XDG_DATA_HOME` before installation to change that location.

### Linux Distribution Packages

The installer uses Python packages from PyPI. On distributions where Python virtual environments are split into a separate package, install that package first. For example, on Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-venv
```

On Fedora:

```bash
sudo dnf install python3
```

The installer creates its own environment and installs the required dependency ranges; distribution packages for `psutil` and `rich` are not required.

### Run Directly From The Repository

This does not install a global command:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python pulsedeck.py
```

The repository also includes `monitor.sh`, which runs the local `pulsedeck.py` beside the script:

```bash
./monitor.sh
```

## Install On Windows

1. Install Python 3.9 or newer from <https://www.python.org/downloads/windows/>. Enable **Add Python to PATH** during setup.
2. Open PowerShell in the repository directory.
3. Allow the installer for the current PowerShell process and run it:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

The installer creates a private virtual environment at `%LOCALAPPDATA%\PulseDeck\venv`, installs PulseDeck and its dependencies from `pyproject.toml`, creates `%LOCALAPPDATA%\PulseDeck\pulsedeck.cmd`, and adds `%LOCALAPPDATA%\PulseDeck` to the current user's `PATH`.

Open a new PowerShell window so the PATH change is loaded, then run:

```powershell
pulsedeck
```

If the command is not found, run it by its full path:

```powershell
& "$env:LOCALAPPDATA\PulseDeck\pulsedeck.cmd"
```

### Run Directly From The Windows Repository

The repository launcher finds `py` first and falls back to `python`:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_windows.ps1
```

For a development environment instead:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python .\pulsedeck.py
```

## Usage

```text
pulsedeck [--once]
```

Start the live dashboard:

```bash
pulsedeck
```

Render one snapshot and exit:

```bash
pulsedeck --once
```

Show command help:

```bash
pulsedeck --help
```

In live mode, press `q` or `Esc` to exit. `Ctrl-C` also stops the process. The terminal is restored when the application exits normally or is interrupted.

For terminals that cannot display the dashboard's Unicode bars, PulseDeck automatically uses ASCII bars. You can force that behavior with:

```bash
PULSEDECK_ASCII=1 pulsedeck
```

## Platform Differences

| Capability | Linux | Windows |
| --- | --- | --- |
| CPU, frequency, memory, swap, processes | Yes | Yes |
| Battery | When exposed by `psutil` | When exposed by `psutil` |
| NVIDIA GPU and GPU processes | With `nvidia-smi` | With `nvidia-smi.exe` in `PATH` |
| AMD/Intel GPU DRM/sysfs metrics | When exposed by Linux | No |
| Linux `/proc` and `/sys` topology details | Yes | No |
| Hardware temperatures | Depends on drivers/sensors | Often unavailable through `psutil` |
| One-minute load average | When provided by Python/OS | Displayed as `0.00` because Windows has no `os.getloadavg()` |
| Konsole autostart | Optional, only when Konsole is installed | No |

`N/A` is normal for optional hardware data. PulseDeck currently uses the first available GPU backend and does not provide multi-GPU rendering.

## Understanding The CPU Columns

- `TOTAL` is the average utilization of all logical CPUs.
- Process `CPU` is normalized to the complete machine capacity. A process using one full thread on an eight-thread machine displays approximately `12.5%`.
- Process `SHARE` is that process's portion of the currently observed CPU work.
- Process `RAM` is the process's percentage of system memory.
- Process `RSS` is the process's resident memory in physical RAM.

See [`docs/METRICS.md`](docs/METRICS.md) for formulas, sampling behavior, and sensor details.

## Documentation And Development

- [`docs/METRICS.md`](docs/METRICS.md): displayed values, formulas, and platform caveats
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): source layout, data flow, installation internals, and testing
- [`CONTRIBUTING.md`](CONTRIBUTING.md): development setup and contribution checks
- [`CHANGELOG.md`](CHANGELOG.md): release history
- [`SECURITY.md`](SECURITY.md): private vulnerability reporting and sensitive output guidance

Run the core checks used by CI:

```bash
python -m unittest discover -s tests -v
python -m py_compile pulsedeck.py
python pulsedeck.py --help
python pulsedeck.py --once
ruff check .
bash -n install.sh monitor.sh
```

On Windows, use the PowerShell or Python equivalents for the Python checks. `bash -n` is only for the two shell scripts and is not required on Windows.

## Limitations And Privacy

- GPU, temperature, battery, network, and disk values depend on operating-system APIs, drivers, permissions, and hardware.
- Only the root filesystem is included in the disk panel.
- Process values are interval samples, not permanent accounting.
- The process table is read-only and no historical graphs are stored.
- PulseDeck does not upload or persist monitoring data. Process command lines can contain private paths, usernames, tokens, or other sensitive arguments; review screenshots and logs before sharing them.

## License

PulseDeck is licensed under the MIT License. See [`LICENSE`](LICENSE) for the complete text.
