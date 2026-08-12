# Day Manager — daily ingestion wrapper for Windows Task Scheduler
#
# This script activates the project venv and runs ingest_all.py.
# Register it with Task Scheduler — see SETUP.md section 7 for the schtasks command.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python      = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script      = Join-Path $ProjectRoot "scripts\ingest_all.py"
$LogFile     = Join-Path $ProjectRoot "logs\scheduler.log"

# Ensure logs directory exists
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "`n[$timestamp] Starting Day Manager ingestion…"

if (-not (Test-Path $Python)) {
    $msg = "[$timestamp] ERROR: venv not found at $Python. Run: uv venv && uv pip install -e ."
    Add-Content -Path $LogFile -Value $msg
    Write-Error $msg
    exit 1
}

if (-not (Test-Path $Script)) {
    $msg = "[$timestamp] ERROR: Script not found at $Script"
    Add-Content -Path $LogFile -Value $msg
    Write-Error $msg
    exit 1
}

& $Python $Script 2>&1 | Tee-Object -FilePath $LogFile -Append

$exit = $LASTEXITCODE
$done = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$done] Finished with exit code $exit"
exit $exit
