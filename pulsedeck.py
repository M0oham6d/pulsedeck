#!/usr/bin/env python3
import argparse
import csv
import os
import platform
import re
import select
import subprocess
import sys
import termios
import time
from datetime import datetime
from pathlib import Path

import psutil
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


REFRESH_SECONDS = 1.0


def read_text(path, default=""):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return default


def cpu_model():
    for line in read_text("/proc/cpuinfo").splitlines():
        if line.startswith("model name"):
            model = line.split(":", 1)[1].strip()
            return model.replace("(R)", "").replace("(TM)", "")
    return platform.processor() or "CPU"


def cpu_topology():
    cores = {}
    for cpu_path in sorted(
        Path("/sys/devices/system/cpu").glob("cpu[0-9]*"),
        key=lambda path: int(path.name[3:]),
    ):
        logical = int(cpu_path.name[3:])
        package = int(read_text(cpu_path / "topology/physical_package_id", "0"))
        core = int(read_text(cpu_path / "topology/core_id", str(logical)))
        cores.setdefault((package, core), []).append(logical)
    if not cores:
        count = psutil.cpu_count(logical=True) or 1
        cores = {(0, i): [i] for i in range(count)}
    return [
        {"package": package, "core": core, "threads": threads}
        for (package, core), threads in sorted(cores.items())
    ]


CPU_MODEL = cpu_model()
CPU_TOPOLOGY = cpu_topology()


def usage_style(percent):
    if percent < 60:
        return "green"
    if percent < 85:
        return "yellow"
    return "red"


def valid_limit(value):
    return value if value is not None and 0 < value <= 200 else None


def temperature_style(sensor, fallback_critical=90):
    current = sensor["current"]
    critical = valid_limit(sensor.get("critical")) or fallback_critical
    if current >= critical * 0.9:
        return "bold red"
    if current >= critical * 0.8:
        return "yellow"
    return "green"


def bar(percent, width=14, style=None):
    percent = max(0.0, min(float(percent), 100.0))
    filled = round(percent / 100 * width)
    result = Text("█" * filled, style=style or usage_style(percent))
    result.append("░" * (width - filled), style="grey23")
    return result


def usage_cell(percent, width=12):
    result = bar(percent, width)
    result.append(f" {percent:5.1f}%", style=usage_style(percent))
    return result


def bytes_value(value):
    value = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{value:.0f} B"
        value /= 1024


def sensor_data():
    sensors = {}
    try:
        for group, entries in psutil.sensors_temperatures().items():
            sensors[group] = [
                {
                    "label": entry.label or f"Sensor {i + 1}",
                    "current": entry.current,
                    "high": entry.high,
                    "critical": entry.critical,
                }
                for i, entry in enumerate(entries)
            ]
    except (AttributeError, OSError):
        pass
    return sensors


def number_or_none(value):
    value = value.strip()
    if not value or "N/A" in value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def gpu_data():
    command = [
        "nvidia-smi",
        "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    row = next(csv.reader(result.stdout.splitlines()), [])
    if len(row) < 6:
        return None
    return {
        "name": row[0].strip(),
        "temp": number_or_none(row[1]),
        "usage": number_or_none(row[2]),
        "memory_used": number_or_none(row[3]),
        "memory_total": number_or_none(row[4]),
        "power": number_or_none(row[5]),
    }


def cpu_data(sensors):
    logical_usage = psutil.cpu_percent(interval=None, percpu=True)
    total_usage = sum(logical_usage) / len(logical_usage) if logical_usage else 0.0
    frequency = psutil.cpu_freq()
    core_sensors = {}
    package_sensor = None
    for sensor in sensors.get("coretemp", []):
        label = sensor["label"].lower()
        if "package" in label:
            package_sensor = sensor
            continue
        match = re.search(r"core\s+(\d+)", label)
        if match:
            core_sensors[int(match.group(1))] = sensor

    cores = []
    for item in CPU_TOPOLOGY:
        values = [
            logical_usage[index]
            for index in item["threads"]
            if index < len(logical_usage)
        ]
        cores.append(
            {
                **item,
                "usage": sum(values) / len(values) if values else 0.0,
                "temperature": core_sensors.get(item["core"]),
            }
        )

    return {
        "model": CPU_MODEL,
        "usage": total_usage,
        "logical_usage": logical_usage,
        "cores": cores,
        "frequency": frequency.current if frequency else None,
        "frequency_max": frequency.max if frequency and frequency.max else None,
        "load": os.getloadavg(),
        "package_temperature": package_sensor,
        "logical_count": len(logical_usage),
    }


def process_data(total_cpu_usage, limit=16):
    rows = []
    logical_cpu_count = psutil.cpu_count(logical=True) or 1
    attributes = ["pid", "name", "cmdline", "cpu_percent", "memory_percent", "memory_info", "status"]
    for process in psutil.process_iter(attributes):
        try:
            info = process.info
            if info["status"] in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                continue
            command = " ".join(info["cmdline"] or []) or f"[{info['name'] or '?'}]"
            raw_cpu = info["cpu_percent"] or 0.0
            cpu_capacity = min(raw_cpu / logical_cpu_count, 100.0)
            cpu_share = (
                min(cpu_capacity / total_cpu_usage * 100, 100.0)
                if total_cpu_usage > 0.1
                else 0.0
            )
            rows.append(
                {
                    "pid": info["pid"],
                    "command": command,
                    "cpu": cpu_capacity,
                    "cpu_share": cpu_share,
                    "memory_percent": info["memory_percent"] or 0.0,
                    "rss": info["memory_info"].rss if info["memory_info"] else 0,
                }
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    rows.sort(key=lambda row: (row["cpu"], row["rss"]), reverse=True)
    return rows[:limit]


def extra_sensor_rows(sensors):
    rows = []
    nvme_index = 1
    for group, entries in sensors.items():
        if group == "coretemp":
            continue
        if group == "nvme":
            for sensor in entries:
                if sensor["label"].lower() == "composite":
                    rows.append((f"NVMe {nvme_index}", sensor))
                    nvme_index += 1
            continue
        if group.startswith("pch") and entries:
            rows.append(("Chipset", entries[0]))
            continue
        if group.startswith("iwlwifi") and entries:
            rows.append(("Wi-Fi", entries[0]))
            continue
        if entries:
            label = group.replace("_", " ").title()
            rows.append((label, entries[0]))
    return rows


def collect():
    sensors = sensor_data()
    memory = psutil.virtual_memory()
    cpu = cpu_data(sensors)
    return {
        "cpu": cpu,
        "gpu": gpu_data(),
        "memory": memory,
        "memory_used": memory.total - memory.available,
        "swap": psutil.swap_memory(),
        "sensors": extra_sensor_rows(sensors),
        "battery": psutil.sensors_battery(),
        "processes": process_data(cpu["usage"]),
    }


def render_cpu(data, compact=False):
    cpu = data["cpu"]
    content = []
    content.append(Text(cpu["model"], style="bold white", overflow="ellipsis", no_wrap=True))

    summary = Text()
    summary.append("TOTAL ", style="dim")
    summary.append(f"{cpu['usage']:5.1f}%", style="bold " + usage_style(cpu["usage"]))
    if cpu["frequency"] is not None:
        summary.append(f"   {cpu['frequency'] / 1000:.2f}", style="bold")
        if cpu["frequency_max"] is not None:
            summary.append(f"/{cpu['frequency_max'] / 1000:.2f}", style="dim")
        summary.append(" GHz", style="dim")
    package = cpu["package_temperature"]
    if package:
        summary.append("   PACKAGE ", style="dim")
        summary.append(f"{package['current']:.0f}°C", style=temperature_style(package, 100))
    summary.append(f"   LOAD {cpu['load'][0]:.2f}", style="dim")
    content.append(summary)

    core_table = Table(
        box=None,
        expand=True,
        padding=(0, 1),
        show_header=True,
        header_style="dim",
    )
    core_table.add_column("CORE", width=6, no_wrap=True)
    if not compact:
        core_table.add_column("THREADS", width=9, no_wrap=True)
    core_table.add_column("USAGE", ratio=1)
    core_table.add_column("TEMP", width=7, justify="right", no_wrap=True)
    for core in cpu["cores"]:
        temperature = core["temperature"]
        temp = Text("N/A", style="dim")
        if temperature:
            temp = Text(
                f"{temperature['current']:.0f}°C",
                style=temperature_style(temperature, 100),
            )
        row = [f"Core {core['core']}"]
        if not compact:
            row.append(",".join(str(thread) for thread in core["threads"]))
        row.extend([usage_cell(core["usage"], 10 if compact else 14), temp])
        core_table.add_row(*row)
    content.append(core_table)
    return Panel(Group(*content), title=" CPU ", border_style="cyan", padding=(0, 1))


def render_gpu(data, compact=False):
    gpu = data["gpu"]
    if gpu is None:
        return Panel(Text("NVIDIA data unavailable", style="dim"), title=" GPU ", border_style="magenta")

    temperature = Text("N/A", style="dim")
    if gpu["temp"] is not None:
        sensor = {"current": gpu["temp"], "critical": 93}
        temperature = Text(f"{gpu['temp']:.0f}°C", style=temperature_style(sensor, 93))
    first = Text(gpu["name"], style="bold white", overflow="ellipsis", no_wrap=True)
    first.append("   ")
    first.append_text(temperature)
    first.append("   POWER ", style="dim")
    first.append(f"{gpu['power']:.0f} W" if gpu["power"] is not None else "N/A")

    usage = gpu["usage"] or 0.0
    used = gpu["memory_used"]
    total = gpu["memory_total"]
    if compact:
        second = Text("GPU  ", style="dim")
        second.append_text(usage_cell(usage, 12))
        second.append("   VRAM ", style="dim")
        if used is not None and total:
            second.append(f"{used:.0f}/{total:.0f} MiB", style="magenta")
        else:
            second.append("N/A", style="dim")
        return Panel(Group(first, second), title=" GPU ", border_style="magenta", padding=(0, 1))

    usage_line = Text("UTIL  ", style="dim")
    usage_line.append_text(usage_cell(usage, 18))
    memory_line = Text("VRAM  ", style="dim")
    if used is not None and total:
        memory_line.append_text(bar(used / total * 100, 18, "magenta"))
        memory_line.append(f" {used:.0f}/{total:.0f} MiB", style="magenta")
    else:
        memory_line.append("N/A", style="dim")
    return Panel(Group(first, usage_line, memory_line), title=" GPU ", border_style="magenta", padding=(0, 1))


def render_memory(data, compact=False):
    memory = data["memory"]
    used = data["memory_used"]
    swap = data["swap"]
    ram_line = Text("RAM   ", style="dim")
    ram_line.append_text(bar(memory.percent, 12 if compact else 18, "green"))
    ram_line.append(f" {bytes_value(used)}/{bytes_value(memory.total)}", style="green")
    swap_line = Text("SWAP  ", style="dim")
    if swap.total:
        swap_line.append_text(bar(swap.percent, 12 if compact else 18, "yellow"))
        swap_line.append(f" {bytes_value(swap.used)}/{bytes_value(swap.total)}", style="yellow")
    else:
        swap_line.append("disabled", style="dim")
    return Panel(Group(ram_line, swap_line), title=" MEMORY ", border_style="green", padding=(0, 1))


def render_sensors(data):
    table = Table.grid(expand=True, padding=(0, 1))
    table.add_column(ratio=1)
    table.add_column(width=8, justify="right")
    for name, sensor in data["sensors"]:
        table.add_row(name, Text(f"{sensor['current']:.0f}°C", style=temperature_style(sensor)))
    battery = data["battery"]
    if battery:
        state = "AC" if battery.power_plugged else "battery"
        table.add_row("Battery", f"{battery.percent:.0f}% {state}")
    if not data["sensors"] and not battery:
        table.add_row("No sensor data", "")
    return Panel(table, title=" SENSORS ", border_style="yellow", padding=(0, 1))


def render_processes(data, compact=False):
    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        padding=(0, 1),
        header_style="bold dim",
        show_edge=False,
    )
    table.add_column("PID", width=7, justify="right", no_wrap=True)
    table.add_column("COMMAND", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("CPU", width=7, justify="right", no_wrap=True)
    table.add_column("SHARE", width=7, justify="right", no_wrap=True)
    if not compact:
        table.add_column("RAM", width=7, justify="right", no_wrap=True)
    table.add_column("RSS", width=10, justify="right", no_wrap=True)
    for process in data["processes"]:
        row = [
            str(process["pid"]),
            Text(process["command"], overflow="ellipsis", no_wrap=True),
            Text(f"{process['cpu']:.1f}%", style=usage_style(process["cpu"])),
            Text(f"{process['cpu_share']:.1f}%", style="cyan"),
        ]
        if not compact:
            row.append(f"{process['memory_percent']:.1f}%")
        row.append(bytes_value(process["rss"]))
        table.add_row(*row)
    return Panel(
        table,
        title=" TOP RESOURCE USERS ",
        subtitle=Text("CPU = total capacity · SHARE = current load", style="dim"),
        border_style="blue",
        padding=(0, 1),
    )


def sensor_footer(data):
    text = Text()
    for index, (name, sensor) in enumerate(data["sensors"]):
        if index:
            text.append("  ·  ", style="dim")
        text.append(f"{name} ", style="dim")
        text.append(f"{sensor['current']:.0f}°C", style=temperature_style(sensor))
    battery = data["battery"]
    if battery:
        if text:
            text.append("  ·  ", style="dim")
        text.append(f"Battery {battery.percent:.0f}%", style="dim")
    text.append("     q / Esc quit", style="dim")
    return text


def build_layout(data, width, height):
    wide = width >= 100 and height >= 28
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=1),
        Layout(name="main"),
        Layout(name="footer", size=1),
    )
    title = Text(
        f" PULSEDECK  //  {platform.node()}  //  {datetime.now():%Y-%m-%d %H:%M:%S} ",
        style="bold cyan",
    )
    layout["header"].update(Align.center(title))

    if wide:
        layout["main"].split_column(
            Layout(name="dashboard", ratio=3),
            Layout(name="processes", ratio=2),
        )
        layout["dashboard"].split_row(
            Layout(name="cpu", ratio=3),
            Layout(name="side", ratio=2),
        )
        layout["side"].split_column(
            Layout(name="gpu", ratio=2),
            Layout(name="memory", ratio=2),
            Layout(name="sensors", ratio=2),
        )
        layout["cpu"].update(render_cpu(data))
        layout["gpu"].update(render_gpu(data))
        layout["memory"].update(render_memory(data))
        layout["sensors"].update(render_sensors(data))
        layout["processes"].update(render_processes(data))
        layout["footer"].update(Align.center(Text("q / Esc  quit", style="dim")))
    else:
        layout["main"].split_column(
            Layout(name="cpu", size=9),
            Layout(name="gpu", size=4),
            Layout(name="memory", size=4),
            Layout(name="processes"),
        )
        layout["cpu"].update(render_cpu(data, compact=True))
        layout["gpu"].update(render_gpu(data, compact=True))
        layout["memory"].update(render_memory(data, compact=True))
        layout["processes"].update(render_processes(data, compact=True))
        layout["footer"].update(Align.center(sensor_footer(data)))
    return layout


def key_pressed():
    if sys.stdin.isatty() and select.select([sys.stdin], [], [], 0)[0]:
        return sys.stdin.read(1)
    return None


def prime_process_counters():
    psutil.cpu_percent(interval=None, percpu=True)
    for process in psutil.process_iter():
        try:
            process.cpu_percent(interval=None)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass


def arguments():
    parser = argparse.ArgumentParser(description="PulseDeck live CPU, GPU, memory, sensor and process monitor")
    parser.add_argument("--once", action="store_true", help="render one snapshot and exit")
    return parser.parse_args()


def main():
    args = arguments()
    console = Console()
    prime_process_counters()
    time.sleep(0.15)
    data = collect()
    if args.once:
        console.print(build_layout(data, console.size.width, max(console.size.height, 30)))
        return

    saved_terminal = None
    if sys.stdin.isatty():
        saved_terminal = termios.tcgetattr(sys.stdin)
        raw_terminal = saved_terminal[:]
        raw_terminal[3] &= ~(termios.ICANON | termios.ECHO)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, raw_terminal)
    try:
        initial = build_layout(data, console.size.width, console.size.height)
        with Live(initial, console=console, screen=True, auto_refresh=False) as live:
            while True:
                started = time.monotonic()
                live.update(
                    build_layout(collect(), console.size.width, console.size.height),
                    refresh=True,
                )
                if key_pressed() in ("q", "Q", "\x1b"):
                    break
                time.sleep(max(0, REFRESH_SECONDS - (time.monotonic() - started)))
    except KeyboardInterrupt:
        pass
    finally:
        if saved_terminal is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, saved_terminal)


if __name__ == "__main__":
    main()
