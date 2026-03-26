# Kimi Autoresearch 安装脚本 (PowerShell)
# Usage: .\install.ps1 [target_directory]

param(
    [string]$TargetDir = ".agents\skills\kimi-autoresearch"
)

Write-Host "Installing Kimi Autoresearch..." -ForegroundColor Green
Write-Host ""

# 检查 Python
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}

if (-not $python) {
    Write-Host "Error: Python 3 is required but not installed." -ForegroundColor Red
    exit 1
}

$pythonVersion = & $python.Source --version 2>&1
Write-Host "✓ Python version: $pythonVersion"

# 检查 Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Error: Git is required but not installed." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Git is available"

# 创建目录
Write-Host ""
Write-Host "Creating directory: $TargetDir"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

# 复制文件
Write-Host "Copying files..."
$items = @("scripts", "references", "examples", ".github", 
           "README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md")

foreach ($item in $items) {
    if (Test-Path $item) {
        Copy-Item -Recurse -Force $item $TargetDir -ErrorAction SilentlyContinue
    }
}

# 验证安装
Write-Host ""
Write-Host "Verifying installation..."
$mainScript = Join-Path $TargetDir "scripts\autoresearch_main.py"

if (Test-Path $mainScript) {
    Write-Host "✓ Installation successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Installed to: $(Resolve-Path $TargetDir)"
    Write-Host ""
    Write-Host "Quick start:"
    Write-Host "  python $mainScript --help"
    Write-Host ""
    Write-Host "Or in Kimi:"
    Write-Host "  `$kimi-autoresearch"
} else {
    Write-Host "✗ Installation may have failed." -ForegroundColor Red
    Write-Host "Please check the target directory."
    exit 1
}

# 添加到 PATH (可选)
Write-Host ""
$addToPath = Read-Host "Add to PATH? (y/N)"
if ($addToPath -eq 'y' -or $addToPath -eq 'Y') {
    $scriptsPath = Resolve-Path (Join-Path $TargetDir "scripts")
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    
    if (-not $currentPath.Contains($scriptsPath)) {
        [Environment]::SetEnvironmentVariable(
            "Path", 
            "$currentPath;$scriptsPath", 
            "User"
        )
        Write-Host "✓ Added to PATH (User)" -ForegroundColor Green
        Write-Host "Please restart your terminal to apply changes."
    } else {
        Write-Host "Already in PATH." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
