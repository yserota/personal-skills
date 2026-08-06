<#
.SYNOPSIS
  Deploy canvas source files from the repo into the Cursor-managed canvases directory.

.DESCRIPTION
  Cursor only detects .canvas.tsx files placed in:
    %USERPROFILE%\.cursor\projects\<workspace-slug>\canvases\

  This script derives that slug automatically from the repo's own path, then
  copies every *.canvas.tsx file from the repo's canvases\ folder into it.

  Run once after cloning, and again whenever you add or update a canvas in the repo.
  The Cursor-managed directory must already exist (Cursor creates it the first time
  you open the workspace).

.EXAMPLE
  .\deploy-canvases.ps1

.NOTES
  The workspace slug is computed from the repo path using Cursor's convention:
    C:\Users\yserota\personal-skills  →  c-Users-yserota-personal-skills
  Algorithm: strip the colon, replace backslashes with dashes, lowercase the drive letter.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# ── Paths ──────────────────────────────────────────────────────────────────────
$repoRoot  = $PSScriptRoot                          # script lives at repo root
$sourceDir = Join-Path $repoRoot "canvases"

# Derive the Cursor project slug from the repo path.
# e.g. C:\Users\yserota\personal-skills → c-Users-yserota-personal-skills
$normalized = $repoRoot.Replace('\', '-').Replace(':', '')
$slug       = $normalized[0].ToString().ToLower() + $normalized.Substring(1)
$targetDir  = Join-Path $env:USERPROFILE ".cursor\projects\$slug\canvases"

# ── Validate ───────────────────────────────────────────────────────────────────
if (-not (Test-Path $sourceDir)) {
    Write-Error "Source directory not found: $sourceDir"
    exit 1
}

$canvases = Get-ChildItem -Path $sourceDir -Filter "*.canvas.tsx" -File
if ($canvases.Count -eq 0) {
    Write-Host "No .canvas.tsx files found in $sourceDir — nothing to deploy."
    exit 0
}

if (-not (Test-Path $targetDir)) {
    Write-Error @"
Cursor canvases directory not found:
  $targetDir

Open this workspace in Cursor at least once so Cursor can create the managed directory,
then re-run this script.
"@
    exit 1
}

# ── Deploy ─────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Deploying $($canvases.Count) canvas(es)"
Write-Host "  from  $sourceDir"
Write-Host "  to    $targetDir"
Write-Host ""

foreach ($file in $canvases) {
    $dest = Join-Path $targetDir $file.Name
    Copy-Item -Path $file.FullName -Destination $dest -Force
    Write-Host "  [+] $($file.Name)"
}

Write-Host ""
Write-Host "Done. Click any canvas link in Cursor chat to open it beside the editor."
