#
# Kimi Autoresearch 打包脚本 (Windows PowerShell)
# 生成 .skill 文件用于分发
#
# 用法:
#   .\package.ps1                    # 使用默认版本号
#   .\package.ps1 -Version 1.1.0     # 指定版本号
#   .\package.ps1 -Version 1.1.0-beta1 -Prerelease
#

param(
    [string]$Version = "1.0.2",
    [switch]$Prerelease,
    [string]$OutputDir = "dist"
)

$PackageName = "kimi-autoresearch"

Write-Host "Packaging Kimi Autoresearch v$Version..." -ForegroundColor Cyan
Write-Host ""

# 创建输出目录
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# 清理旧文件
Remove-Item "$OutputDir\${PackageName}-*.skill" -ErrorAction SilentlyContinue
Remove-Item "$OutputDir\${PackageName}-*.sha256" -ErrorAction SilentlyContinue

# 创建临时目录
$TmpDir = New-TemporaryFile | ForEach-Object { Remove-Item $_; New-Item -ItemType Directory -Path $_ }
$PackageDir = Join-Path $TmpDir $PackageName

# 复制文件
Write-Host "Copying files..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

$ItemsToCopy = @(
    "scripts",
    "references",
    "examples",
    ".github",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SKILL.md",
    "package.sh",
    "package.ps1"
)

foreach ($item in $ItemsToCopy) {
    if (Test-Path $item) {
        Copy-Item -Path $item -Destination $PackageDir -Recurse -Force
    }
}

# 复制可选文档
$OptionalDocs = @("GAP_ANALYSIS.md", "COMPLETION_REPORT.md")
foreach ($doc in $OptionalDocs) {
    if (Test-Path $doc) {
        Copy-Item -Path $doc -Destination $PackageDir -Force
    }
}

# 创建 .skill 文件 (zip 格式)
Write-Host "Creating .skill package..." -ForegroundColor Yellow
$SkillFile = "${PackageName}-${Version}.skill"
$SkillPath = Join-Path $OutputDir $SkillFile

# 使用 .NET 压缩
Add-Type -AssemblyName System.IO.Compression.FileSystem
$CompressionLevel = [System.IO.Compression.CompressionLevel]::Optimal

# 创建 zip
$ZipPath = Join-Path $TmpDir "${SkillFile}.zip"
[System.IO.Compression.ZipFile]::CreateFromDirectory($PackageDir, $ZipPath, $CompressionLevel, $false)

# 重命名为 .skill
Move-Item -Path $ZipPath -Destination $SkillPath -Force

# 计算 SHA256 校验和
$Hash = Get-FileHash -Path $SkillPath -Algorithm SHA256
$HashFile = Join-Path $OutputDir "${PackageName}-${Version}.sha256"
"$($Hash.Hash)  $SkillFile" | Out-File -FilePath $HashFile -Encoding UTF8

# 同时创建 latest 版本
$LatestSkill = Join-Path $OutputDir "${PackageName}-latest.skill"
Copy-Item -Path $SkillPath -Destination $LatestSkill -Force

Write-Host ""
Write-Host "✓ Package created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Output files:" -ForegroundColor Cyan
Get-ChildItem -Path $OutputDir | ForEach-Object {
    $size = "{0:N0}" -f $_.Length
    Write-Host "  $($_.Name) ($size bytes)"
}
Write-Host ""
Write-Host "Checksum:" -ForegroundColor Cyan
Get-Content $HashFile
Write-Host ""
Write-Host "Install with:" -ForegroundColor Cyan
Write-Host "  Expand-Archive -Path '$SkillPath' -DestinationPath '`$env:USERPROFILE\.agents\skills\'"

# 清理临时目录
Remove-Item -Path $TmpDir -Recurse -Force

# 返回文件路径
@{
    SkillFile = $SkillPath
    HashFile = $HashFile
    Version = $Version
}
