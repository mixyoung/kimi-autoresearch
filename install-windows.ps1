# Kimi Autoresearch Windows Install Script
# Run as admin: PowerShell -ExecutionPolicy Bypass -File install-windows.ps1

param([string]$Source = (Get-Location).Path)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kimi Autoresearch Windows Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) {
    Write-Host "[WARNING] Run as admin for best experience" -ForegroundColor Yellow
    Write-Host ""
}

# Find skill directory
$SkillDir = $null
$paths = @(
    "$env:USERPROFILE\.config\agents\skills",
    "$env:USERPROFILE\.agents\skills",
    "$env:USERPROFILE\.kimi\skills",
    "$env:USERPROFILE\.claude\skills"
)

foreach ($p in $paths) {
    if (Test-Path $p) {
        $SkillDir = $p
        break
    }
}

if (-not $SkillDir) {
    $SkillDir = "$env:USERPROFILE\.agents\skills"
}

Write-Host "Source: $Source" -ForegroundColor Green
Write-Host "Target: $SkillDir" -ForegroundColor Green
Write-Host ""

# Create directory
if (-not (Test-Path $SkillDir)) {
    New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
    Write-Host "Created: $SkillDir" -ForegroundColor Yellow
}

$Target = Join-Path $SkillDir "kimi-autoresearch"

# Check existing
if (Test-Path $Target) {
    Write-Host "Already exists: $Target" -ForegroundColor Yellow
    $resp = Read-Host "Replace? (y/N)"
    if ($resp -eq "y" -or $resp -eq "Y") {
        Remove-Item $Target -Recurse -Force
        Write-Host "Removed old version" -ForegroundColor Yellow
    }
    else {
        Write-Host "Cancelled" -ForegroundColor Red
        exit 0
    }
}

# Try symlink (needs admin)
$success = $false
try {
    New-Item -ItemType SymbolicLink -Path $Target -Target $Source -ErrorAction Stop | Out-Null
    $success = $true
    Write-Host "[OK] Symbolic link created" -ForegroundColor Green
}
catch {
    Write-Host "[INFO] Admin required for symlink, using copy..." -ForegroundColor Yellow
}

# Fallback to copy
if (-not $success) {
    try {
        Copy-Item -Path $Source -Destination $Target -Recurse -Force -ErrorAction Stop
        Write-Host "[OK] Files copied" -ForegroundColor Green
    }
    catch {
        Write-Error "Install failed: $_"
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Install successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Now you can use in Kimi:" -ForegroundColor Cyan
Write-Host "  `$kimi-autoresearch" -ForegroundColor White
Write-Host ""

# Optional: Add to PATH
$addPath = Read-Host "Add to PATH? (y/N)"
if ($addPath -eq "y" -or $addPath -eq "Y") {
    $scriptsDir = Join-Path $Target "scripts"
    $current = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($current -notlike "*$scriptsDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$current;$scriptsDir", "User")
        Write-Host "[OK] Added to PATH (restart terminal)" -ForegroundColor Green
    }
}
