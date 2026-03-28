#!/usr/bin/env python3
"""
Git status checker for autoresearch.
"""
import subprocess
import sys


def run_git(args: list[str]) -> tuple[int, str]:
    """Run a git command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, str(e)


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    code, _ = run_git(['rev-parse', '--git-dir'])
    return code == 0


def has_changes() -> bool:
    """Check if there are uncommitted changes."""
    code, output = run_git(['status', '--porcelain'])
    if code != 0:
        return False
    return len(output.strip()) > 0


def get_current_commit() -> str:
    """Get current commit hash (short)."""
    code, output = run_git(['rev-parse', '--short', 'HEAD'])
    if code == 0:
        return output.strip()
    return "unknown"


def stash_changes() -> bool:
    """Stash current changes."""
    code, _ = run_git(['stash', 'push', '-m', 'autoresearch-auto-stash'])
    return code == 0


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check git status')
    parser.add_argument('--action', type=str, required=True,
                       choices=['check', 'commit', 'revert', 'stash', 'commit-hash'])
    parser.add_argument('--message', type=str, default='autoresearch: iteration')
    
    args = parser.parse_args()
    
    if not is_git_repo():
        print("Error: Not a git repository", file=sys.stderr)
        sys.exit(1)
    
    if args.action == 'check':
        if has_changes():
            print("has_changes")
            sys.exit(0)
        else:
            print("clean")
            sys.exit(0)
    
    elif args.action == 'commit-hash':
        print(get_current_commit())
        sys.exit(0)
    
    elif args.action == 'stash':
        if has_changes():
            if stash_changes():
                print("stashed")
                sys.exit(0)
            else:
                print("Error: Failed to stash", file=sys.stderr)
                sys.exit(1)
        else:
            print("nothing_to_stash")
            sys.exit(0)
    
    elif args.action == 'commit':
        # Stage all changes
        code1, _ = run_git(['add', '-A'])
        if code1 != 0:
            print("Error: Failed to stage changes", file=sys.stderr)
            sys.exit(1)
        
        # Commit
        code2, output = run_git(['commit', '-m', args.message])
        if code2 != 0:
            print(f"Error: Failed to commit: {output}", file=sys.stderr)
            sys.exit(1)
        
        commit_hash = get_current_commit()
        print(f"committed:{commit_hash}")
        sys.exit(0)
    
    elif args.action == 'revert':
        # Revert last commit
        code, output = run_git(['revert', '--no-edit', 'HEAD'])
        if code != 0:
            # Try reset if revert fails
            code2, _ = run_git(['reset', '--hard', 'HEAD~1'])
            if code2 != 0:
                print(f"Error: Failed to revert: {output}", file=sys.stderr)
                sys.exit(1)
        
        print("reverted")
        sys.exit(0)


if __name__ == '__main__':  # pragma: no cover
    main()
