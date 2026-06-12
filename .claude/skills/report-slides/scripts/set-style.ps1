# set-style.ps1 <name> — copy a built-in style as the project default.
# Run from the project root:
#   & (Get-ChildItem $env:USERPROFILE\.claude -Recurse -Filter set-style.ps1 |
#       Where-Object FullName -like '*report-slides*' | Select-Object -First 1).FullName paper

param([string]$Style = "")

if (-not $Style) {
    Write-Host "Usage: set-style.ps1 <name>"
    Write-Host "Built-in styles: default  minimal  dark  paper"
    exit 1
}

$src = Get-ChildItem $env:USERPROFILE\.claude -Recurse -Filter "$Style.md" |
    Where-Object FullName -like "*report-slides*styles*" | Select-Object -First 1

if (-not $src) {
    Write-Host "Error: style '$Style' not found."
    Write-Host "Built-in styles: default  minimal  dark  paper"
    exit 1
}

New-Item -ItemType Directory -Force -Path "docs\slides" | Out-Null
Copy-Item $src.FullName "docs\slides\_style.md" -Force
Write-Host "Style set: docs\slides\_style.md  ($Style)"
