# PulseDeck Metrics

This document explains what each value means and how PulseDeck calculates it.

## CPU Panel

### Total CPU Usage

PulseDeck reads usage for every logical CPU using:

```python
logical_usage = psutil.cpu_percent(interval=None, percpu=True)
total_usage = sum(logical_usage) / len(logical_usage)
```

`TOTAL` is therefore the average utilization of the complete CPU. On an eight-thread CPU, four fully busy threads and four idle threads produce approximately 50% total usage.

### Frequency

The CPU line displays current and maximum frequency:

```text
1.30/4.10 GHz
```

Frequency can change quickly because of power management, Turbo Boost, workload, and thermal limits.

### Package Temperature

`PACKAGE` is the temperature reported for the whole CPU package by the Linux `coretemp` driver. It is not the temperature of a single core.

### Load Average

`LOAD` is the one-minute Linux load average returned by `os.getloadavg()`.

Load average is not the same as CPU utilization. It represents runnable or waiting work, so disk or other resource contention can increase load even when CPU usage is not 100%.

### Physical Cores And Logical Threads

PulseDeck reads CPU topology from:

```text
/sys/devices/system/cpu/cpu*/topology/physical_package_id
/sys/devices/system/cpu/cpu*/topology/core_id
```

For a four-core/eight-thread CPU, the mapping may be:

```text
Physical Core 0 -> logical CPUs 0 and 4
Physical Core 1 -> logical CPUs 1 and 5
Physical Core 2 -> logical CPUs 2 and 6
Physical Core 3 -> logical CPUs 3 and 7
```

Each physical-core usage value is the average of its logical threads. Temperature values are matched by labels such as `Core 0`, not by assuming sensor order.

## Process CPU Values

The process table contains two CPU columns: `CPU` and `SHARE`.

### CPU: Total Machine Capacity

Operating-system process APIs commonly report 100% when a process fully occupies one logical CPU. On an eight-logical-CPU machine, that is 12.5% of the complete machine capacity.

PulseDeck normalizes the raw value:

```python
cpu_capacity = raw_cpu_percent / logical_cpu_count
```

Example:

```text
Raw process value:       100%
Logical CPU count:         8
PulseDeck CPU value:      12.5%
```

The `CPU` column answers:

> What percentage of the entire CPU capacity is this process using?

The displayed value is constrained to 0% through 100%.

### SHARE: Current CPU Work

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

This means that the process accounts for approximately 42.9% of the CPU work observed in that sample. It does not mean the entire CPU is 42.9% busy.

`SHARE` can be high while total CPU usage is low. That is expected when one process is responsible for most of the small amount of active work. Use `CPU` to judge whether the complete machine is heavily loaded.

The visible process rows do not necessarily add up to 100% `SHARE`, because only the top processes are shown and some processes may be inaccessible.

### RAM And RSS

`RAM` is a process's percentage of system memory.

`RSS` means resident set size: memory from that process currently resident in physical RAM. RSS values from multiple processes should not be added as an exact total because shared memory can appear in more than one process.

## GPU Metrics

GPU data is collected with:

```bash
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits
```

The GPU panel displays:

- GPU name
- GPU temperature
- GPU utilization
- Used and total VRAM
- Power draw when supported

Some laptop GPUs do not expose power draw. PulseDeck displays `N/A` instead of `0 W`, because zero would be misleading.

If `nvidia-smi` is unavailable, CPU and system metrics continue working while the GPU panel reports unavailable data.

## Memory Metrics

RAM usage is calculated as:

```python
memory_used = memory.total - memory.available
```

The memory panel shows RAM and swap used/total values and percentage bars.

## Temperature Sensors

PulseDeck reads `psutil.sensors_temperatures()` and maps common Linux sensor groups to readable labels:

| Linux group | Display label |
| --- | --- |
| `coretemp` | CPU package and physical-core temperatures |
| `nvme` | NVMe 1, NVMe 2, and so on |
| `pch_*` | Chipset |
| `iwlwifi_*` | Wi-Fi |
| Other groups | Converted sensor group name |

If a sensor supplies a critical limit, PulseDeck uses it. Otherwise, general sensors use a 90°C fallback.

Temperature colors use these thresholds:

- Green: below 80% of the critical limit
- Yellow: at least 80% of the critical limit
- Red: at least 90% of the critical limit

## Sampling

At startup, PulseDeck primes the `psutil` CPU counters and waits briefly before collecting the first real sample. This avoids the usual first-sample problem where process CPU values are zero or unreliable.

The live refresh interval is approximately one second and is configured by:

```python
REFRESH_SECONDS = 1.0
```

Measurements are samples. They can change between refreshes as processes start, stop, sleep, migrate between CPUs, or change frequency.
