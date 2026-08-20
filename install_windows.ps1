$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallDir = Join-Path $env:LOCALAPPDATA "PulseDeck"
$VenvDir = Join-Path $InstallDir "venv"
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python 3 was not found. Install Python from https://www.python.org/downloads/windows/ and try again."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
    if ($Python.Name -eq "py.exe") {
        & $Python.Source -3 -m venv $VenvDir
    } else {
        & $Python.Source -m venv $VenvDir
    }
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
& $VenvPython -m pip install -r (Join-Path $ProjectDir "requirements.txt")
Copy-Item (Join-Path $ProjectDir "pulsedeck.py") (Join-Path $InstallDir "pulsedeck.py") -Force

$Launcher = Join-Path $InstallDir "pulsedeck.cmd"
$LauncherContent = "@echo off`r`n`"$VenvPython`" `"$InstallDir\pulsedeck.py`" %*`r`n"
Set-Content -Path $Launcher -Value $LauncherContent -Encoding ASCII

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathEntries = @($UserPath -split ";" | Where-Object { $_ })
if ($PathEntries -notcontains $InstallDir) {
    [Environment]::SetEnvironmentVariable("Path", (($PathEntries + $InstallDir) -join ";"), "User")
    Write-Host "Added $InstallDir to the user PATH. Open a new terminal before running pulsedeck."
}

Write-Host "PulseDeck installed to $InstallDir"
Write-Host "Run it with: pulsedeck"
Write-Host "Run one snapshot with: pulsedeck --once"
