# Contributing

## Development Setup

PulseDeck supports Python 3.9 and newer on Linux and Windows. On Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Run the local checks before opening a change:

```bash
python -m unittest discover -s tests -v
python -m py_compile pulsedeck.py
python pulsedeck.py --help
python pulsedeck.py --once
bash -n install.sh monitor.sh
ruff check .
```

On Windows, run the Python checks above from the activated environment. The `bash -n` command is only applicable when Bash is available; it checks the Linux shell scripts and is not required for Windows-only changes.

Keep platform-specific collectors tolerant of missing drivers, sensors, files, and permissions.
Changes to displayed metrics should update `docs/METRICS.md` and include focused tests.

## Pull Requests

Describe the user-visible behavior, supported platforms tested, and verification commands used.
Do not include screenshots containing private process command lines without reviewing them first.
