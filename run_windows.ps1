$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python 3 was not found."
}

if ($Python.Name -eq "py.exe") {
    & $Python.Source -3 (Join-Path $ProjectDir "pulsedeck.py") $args
} else {
    & $Python.Source (Join-Path $ProjectDir "pulsedeck.py") $args
}
