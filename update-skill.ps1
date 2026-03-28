#!/usr/bin/env powershell
# 一键更新 kimi-autoresearch skill

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Kimi Autoresearch Skill Updater v2.0"
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$skillDir = "$env:USERPROFILE\.agents\skills\kimi-autoresearch"
$sourceDir = "E:\33_dev_env\kimi-autoresearch"

# 检查源目录
if (!(Test-Path $sourceDir)) {
    Write-Host "❌ 错误: 找不到源目录 $sourceDir" -ForegroundColor Red
    Write-Host "   请确认当前目录是否正确" -ForegroundColor Red
    exit 1
}

# 检查是否已安装
if (!(Test-Path $skillDir)) {
    Write-Host "⚠️  未检测到已安装版本" -ForegroundColor Yellow
    Write-Host "   将执行全新安装..." -ForegroundColor Yellow
} else {
    Write-Host "✓ 检测到已安装版本" -ForegroundColor Green
    
    # 备份旧版本
    $backupDir = "$env:USERPROFILE\.agents\skills\kimi-autoresearch.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Write-Host "📦 备份旧版本到: $backupDir" -ForegroundColor Cyan
    Copy-Item -Path $skillDir -Destination $backupDir -Recurse -Force
}

Write-Host ""
Write-Host "🔄 开始更新..." -ForegroundColor Cyan
Write-Host ""

# 如果存在，删除旧版本
if (Test-Path $skillDir) {
    Remove-Item -Path $skillDir -Recurse -Force
}

# 复制新版本
Copy-Item -Path $sourceDir -Destination $skillDir -Recurse -Force

# 验证安装
if (Test-Path "$skillDir\SKILL.md") {
    $version = Select-String -Path "$skillDir\SKILL.md" -Pattern "version-[0-9]+\.[0-9]+\.[0-9]+" | ForEach-Object { $_.Matches[0].Value }
    Write-Host "✅ 更新成功！" -ForegroundColor Green
    Write-Host "   版本: $version" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 使用方法:" -ForegroundColor Cyan
    Write-Host "   1. 重启 Kimi Code CLI" -ForegroundColor White
    Write-Host "   2. 输入: `$kimi-autoresearch`" -ForegroundColor White
    Write-Host "   3. 输入 Goal 和 Verify" -ForegroundColor White
    Write-Host "   4. 现在默认无限迭代！" -ForegroundColor White
} else {
    Write-Host "❌ 更新失败！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
