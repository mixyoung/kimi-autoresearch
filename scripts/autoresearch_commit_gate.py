#!/usr/bin/env python3
"""
Commit gate for autoresearch - validates scope before committing changes.

Checks git/worktree safety across all managed repos before allowing commits.
This prevents partial commits or conflicts during parallel experiments.
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Optional


def run_git(args: list[str], cwd: Optional[str] = None) -> tuple[int, str]:
    """Run git command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, str(e)


def is_git_repo(cwd: Optional[str] = None) -> bool:
    """Check if directory is a git repository."""
    code, _ = run_git(['rev-parse', '--git-dir'], cwd=cwd)
    return code == 0


def get_git_status(cwd: Optional[str] = None) -> dict:
    """Get comprehensive git status."""
    status = {
        'is_repo': False,
        'branch': None,
        'is_detached': False,
        'has_changes': False,
        'untracked_files': [],
        'staged_files': [],
        'unstaged_files': [],
        'can_commit': False,
        'errors': []
    }
    
    if not is_git_repo(cwd):
        status['errors'].append("Not a git repository")
        return status
    
    status['is_repo'] = True
    
    # Check for detached HEAD
    code, output = run_git(['symbolic-ref', '--short', 'HEAD'], cwd=cwd)
    if code != 0:
        status['is_detached'] = True
        status['errors'].append("Detached HEAD - cannot commit")
    else:
        status['branch'] = output.strip()
    
    # Check status
    code, output = run_git(['status', '--porcelain'], cwd=cwd)
    if code == 0:
        # Don't strip leading whitespace - it's part of the format
        lines = output.split('\n') if output else []
        lines = [line for line in lines if line]  # Remove empty lines only
        
        for line in lines:
            if not line:
                continue
            # Parse porcelain output
            # XY PATH or XY ORIG_PATH -> PATH
            if len(line) >= 3:
                x, y = line[0], line[1]
                filepath = line[3:]
                
                if x in 'MADRC':
                    status['staged_files'].append(filepath)
                if y in 'MD':
                    status['unstaged_files'].append(filepath)
                if x == '?' and y == '?':
                    status['untracked_files'].append(filepath)
        
        status['has_changes'] = len(lines) > 0
    
    # Determine if can commit
    status['can_commit'] = (
        status['is_repo'] and
        not status['is_detached'] and
        status['branch'] is not None
    )
    
    return status


def check_scope_safety(scope: str, cwd: Optional[str] = None) -> dict:
    """Check if scope is safe to modify."""
    result = {
        'scope': scope,
        'files': [],
        'exists': False,
        'is_safe': False,
        'warnings': [],
        'errors': []
    }
    
    # Expand glob pattern
    import glob
    if cwd:
        pattern = os.path.join(cwd, scope)
    else:
        pattern = scope
    
    files = glob.glob(pattern, recursive=True)
    result['files'] = files
    result['exists'] = len(files) > 0
    
    if not files:
        result['errors'].append(f"No files match scope: {scope}")
        return result
    
    # Check for protected files
    protected_patterns = [
        '.git',
        'node_modules',
        '__pycache__',
        '.venv',
        'venv',
    ]
    
    for f in files:
        for protected in protected_patterns:
            if protected in f:
                result['warnings'].append(f"Scope includes protected path: {f}")
    
    # Check if files are tracked by git
    for f in files[:10]:  # Check first 10 files
        file_dir = os.path.dirname(f) or '.'
        if is_git_repo(file_dir):
            rel_path = os.path.relpath(f, file_dir)
            code, _ = run_git(['ls-files', '--error-unmatch', rel_path], cwd=file_dir)
            if code != 0:
                result['warnings'].append(f"File not tracked by git: {f}")
    
    result['is_safe'] = len(result['errors']) == 0
    return result


def commit_gate_check(
    scope: Optional[str] = None,
    companion_repos: Optional[list[str]] = None,
    strict: bool = False
) -> dict:
    """
    Run commit gate checks.
    
    Args:
        scope: File scope to check
        companion_repos: Additional repos to check
        strict: Fail on warnings if True
        
    Returns:
        Check results dict
    """
    result = {
        'passed': False,
        'primary_repo': {},
        'companion_repos': {},
        'scope_check': {},
        'errors': [],
        'warnings': []
    }
    
    # Check primary repo
    git_status = get_git_status()
    result['primary_repo'] = git_status
    
    if not git_status['is_repo']:
        result['errors'].append("Primary directory is not a git repository")
        return result
    
    if not git_status['can_commit']:
        result['errors'].extend(git_status['errors'])
    
    # Check companion repos
    if companion_repos:
        for repo_path in companion_repos:
            if os.path.isdir(repo_path):
                repo_status = get_git_status(repo_path)
                result['companion_repos'][repo_path] = repo_status
                
                if not repo_status['can_commit']:
                    result['errors'].append(f"Companion repo not safe: {repo_path}")
    
    # Check scope
    if scope:
        scope_result = check_scope_safety(scope)
        result['scope_check'] = scope_result
        
        if not scope_result['is_safe']:
            result['errors'].extend(scope_result['errors'])
        
        result['warnings'].extend(scope_result['warnings'])
    
    # Determine if passed
    result['passed'] = len(result['errors']) == 0
    
    if strict and result['warnings']:
        result['passed'] = False
        result['errors'].extend([f"WARNING (strict mode): {w}" for w in result['warnings']])
    
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Commit gate - validates safety before committing changes'
    )
    parser.add_argument('--scope', type=str, help='File scope to check')
    parser.add_argument('--companion-repo', type=str, action='append',
                       help='Additional repo to check (can be repeated)')
    parser.add_argument('--strict', action='store_true',
                       help='Fail on warnings')
    parser.add_argument('--json', action='store_true',
                       help='Output JSON')
    parser.add_argument('--quiet', action='store_true',
                       help='Only output errors')
    
    args = parser.parse_args()
    
    result = commit_gate_check(
        scope=args.scope,
        companion_repos=args.companion_repo,
        strict=args.strict
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    elif not args.quiet:
        print("=" * 60)
        print("Commit Gate Check")
        print("=" * 60)
        
        # Primary repo
        primary = result['primary_repo']
        print(f"\nPrimary Repository:")
        print(f"  Branch: {primary.get('branch', 'N/A')}")
        print(f"  Detached HEAD: {primary.get('is_detached', False)}")
        print(f"  Has changes: {primary.get('has_changes', False)}")
        
        # Scope
        if result['scope_check']:
            scope = result['scope_check']
            print(f"\nScope Check ({scope['scope']}):")
            print(f"  Files found: {len(scope['files'])}")
            print(f"  Is safe: {scope['is_safe']}")
        
        # Companion repos
        if result['companion_repos']:
            print(f"\nCompanion Repositories:")
            for path, status in result['companion_repos'].items():
                print(f"  {path}: {status.get('branch', 'N/A')}")
        
        # Result
        print("\n" + "=" * 60)
        if result['passed']:
            print("✓ PASSED - Safe to commit")
        else:
            print("✗ FAILED - Issues found")
        
        # Errors and warnings
        if result['errors']:
            print("\nErrors:")
            for e in result['errors']:
                print(f"  ✗ {e}")
        
        if result['warnings'] and not args.strict:
            print("\nWarnings:")
            for w in result['warnings']:
                print(f"  ⚠ {w}")
    
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
