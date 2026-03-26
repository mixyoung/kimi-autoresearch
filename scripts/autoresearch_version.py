#!/usr/bin/env python3
"""
Kimi Autoresearch 版本管理工具
用于更新版本号、创建 tag、生成 CHANGELOG

用法:
    python scripts/autoresearch_version.py bump patch    # 1.0.0 -> 1.0.1
    python scripts/autoresearch_version.py bump minor    # 1.0.0 -> 1.1.0
    python scripts/autoresearch_version.py bump major    # 1.0.0 -> 2.0.0
    python scripts/autoresearch_version.py set 1.2.3     # 设置指定版本
    python scripts/autoresearch_version.py show          # 显示当前版本
    python scripts/autoresearch_version.py tag           # 创建 git tag
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_project_root():
    """获取项目根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent


def get_current_version():
    """从 package.sh 读取当前版本"""
    package_sh = get_project_root() / "package.sh"
    if package_sh.exists():
        content = package_sh.read_text(encoding='utf-8')
        match = re.search(r'VERSION="(\d+\.\d+\.\d+)"', content)
        if match:
            return match.group(1)
    return "1.0.0"


def bump_version(version, part):
    """递增版本号"""
    parts = version.split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if part == 'major':
        return f"{major + 1}.0.0"
    elif part == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_file_version(file_path, pattern, replacement, new_version):
    """更新文件中的版本号"""
    if not file_path.exists():
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
    except Exception as e:
        print(f"⚠️  更新 {file_path} 失败: {e}")
    return False


def update_all_versions(old_version, new_version):
    """更新所有文件中的版本号"""
    root = get_project_root()
    updated = []
    
    # package.sh
    if update_file_version(
        root / "package.sh",
        rf'VERSION="{old_version}"',
        f'VERSION="{new_version}"',
        new_version
    ):
        updated.append("package.sh")
    
    # package.ps1
    if update_file_version(
        root / "package.ps1",
        rf'\$Version = "{old_version}"',
        f'$Version = "{new_version}"',
        new_version
    ):
        updated.append("package.ps1")
    
    # SKILL.md 和 README.md (徽章)
    for md_file in ["SKILL.md", "README.md"]:
        if update_file_version(
            root / md_file,
            rf'version-{old_version}',
            f'version-{new_version}',
            new_version
        ):
            updated.append(md_file)
    
    return updated


def update_changelog(new_version, changes=None):
    """更新 CHANGELOG.md"""
    root = get_project_root()
    changelog = root / "CHANGELOG.md"
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    new_section = f"## [{new_version}] - {today}\n\n"
    if changes:
        new_section += changes + "\n\n"
    else:
        new_section += "### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n"
    
    if changelog.exists():
        content = changelog.read_text(encoding='utf-8')
        # 在第一个 ## 之前插入新版本
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('## ['):
                insert_idx = i
                break
        
        lines.insert(insert_idx, new_section.rstrip())
        changelog.write_text('\n'.join(lines), encoding='utf-8')
    else:
        # 创建新的 CHANGELOG
        content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

{new_section}"""
        changelog.write_text(content, encoding='utf-8')
    
    return changelog.name


def create_git_tag(version, message=None):
    """创建 git tag"""
    root = get_project_root()
    os.chdir(root)
    
    tag = f"v{version}"
    if not message:
        message = f"Release {tag}"
    
    try:
        # 检查是否有未提交的更改
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, encoding='utf-8', errors='ignore'
        )
        if result.stdout.strip():
            print("⚠️  有未提交的更改，请先提交:")
            print(result.stdout)
            return False
        
        # 创建 tag
        subprocess.run(['git', 'tag', '-a', tag, '-m', message], check=True)
        print(f"✅ Created tag: {tag}")
        print(f"   推送到远程: git push origin {tag}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 创建 tag 失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Kimi Autoresearch 版本管理工具"
    )
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # bump 命令
    bump_parser = subparsers.add_parser('bump', help='递增版本号')
    bump_parser.add_argument(
        'part', choices=['patch', 'minor', 'major'],
        help='要递增的部分'
    )
    bump_parser.add_argument(
        '--no-changelog', action='store_true',
        help='不更新 CHANGELOG'
    )
    bump_parser.add_argument(
        '--tag', action='store_true',
        help='自动创建 git tag'
    )
    
    # set 命令
    set_parser = subparsers.add_parser('set', help='设置指定版本')
    set_parser.add_argument('version', help='版本号 (例如: 1.2.3)')
    set_parser.add_argument('--tag', action='store_true', help='自动创建 git tag')
    
    # show 命令
    subparsers.add_parser('show', help='显示当前版本')
    
    # tag 命令
    tag_parser = subparsers.add_parser('tag', help='创建 git tag')
    tag_parser.add_argument('-m', '--message', help='Tag 消息')
    
    args = parser.parse_args()
    
    if args.command == 'show' or args.command is None:
        version = get_current_version()
        print(f"📦 Current version: {version}")
        return
    
    if args.command == 'bump':
        old_version = get_current_version()
        new_version = bump_version(old_version, args.part)
        
        print(f"🔄 Bumping {args.part}: {old_version} -> {new_version}")
        
        # 更新所有文件
        updated = update_all_versions(old_version, new_version)
        print(f"✅ Updated: {', '.join(updated)}")
        
        # 更新 CHANGELOG
        if not args.no_changelog:
            update_changelog(new_version)
            print(f"✅ Updated CHANGELOG.md")
        
        # 创建 tag
        if args.tag:
            create_git_tag(new_version)
        
        print(f"\n🎉 Version bumped to {new_version}")
        if not args.tag:
            print(f"   创建 tag: python scripts/autoresearch_version.py tag")
    
    elif args.command == 'set':
        old_version = get_current_version()
        new_version = args.version
        
        print(f"🔄 Setting version: {old_version} -> {new_version}")
        
        updated = update_all_versions(old_version, new_version)
        print(f"✅ Updated: {', '.join(updated)}")
        
        if args.tag:
            create_git_tag(new_version)
    
    elif args.command == 'tag':
        version = get_current_version()
        create_git_tag(version, args.message)


if __name__ == '__main__':
    main()
