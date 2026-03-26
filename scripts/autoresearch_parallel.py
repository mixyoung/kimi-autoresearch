#!/usr/bin/env python3
"""
Parallel experiments using git worktrees.
Tests multiple hypotheses simultaneously.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Optional, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class ParallelExperiment:
    def __init__(self, base_dir: str, max_workers: int = 3):
        self.base_dir = os.path.abspath(base_dir)
        self.max_workers = max_workers
        self.worktrees = []
        self.results = []
    
    def run_git(self, args: list, cwd: Optional[str] = None) -> tuple[int, str]:
        """Run git command."""
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=cwd or self.base_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            return -1, str(e)
    
    def create_worktree(self, name: str, hypothesis: dict) -> Optional[str]:
        """Create a git worktree for a hypothesis."""
        worktree_path = os.path.join(self.base_dir, f'.autoresearch-worktree-{name}')
        
        # Remove existing if present
        if os.path.exists(worktree_path):
            shutil.rmtree(worktree_path)
        
        # Create worktree
        code, output = self.run_git([
            'worktree', 'add', '-b', f'autoresearch-{name}', worktree_path
        ])
        
        if code != 0:
            print(f"Failed to create worktree {name}: {output}")
            return None
        
        self.worktrees.append({
            'name': name,
            'path': worktree_path,
            'hypothesis': hypothesis
        })
        
        return worktree_path
    
    def apply_hypothesis(self, worktree: dict[str, Any]) -> bool:
        """Apply hypothesis changes to worktree."""
        # This is a placeholder - in practice, you'd apply specific changes
        # based on the hypothesis type
        print(f"Applying hypothesis to {worktree['name']}: {worktree['hypothesis']['description']}")
        return True
    
    def run_verification(self, worktree: dict[str, Any], verify_cmd: str) -> dict[str, Any]:
        """Run verification in a worktree."""
        try:
            result = subprocess.run(
                verify_cmd,
                shell=True,
                cwd=worktree['path'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Extract metric
            import re
            metric = None
            for pattern in [r'(\d+\.?\d*)%', r'(\d+\.?\d*)']:
                match = re.search(pattern, result.stdout)
                if match:
                    try:
                        metric = float(match.group(1))
                        break
                    except:
                        pass
            
            return {
                'success': result.returncode == 0,
                'metric': metric,
                'output': result.stdout[:500],
                'worktree': worktree['name']
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Timeout',
                'worktree': worktree['name']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'worktree': worktree['name']
            }
    
    def run_parallel(self, hypotheses: list[dict[str, Any]], verify_cmd: str) -> dict[str, Any]:
        """Run hypotheses in parallel."""
        print(f"Running {len(hypotheses)} hypotheses in parallel...")
        
        # Create worktrees
        for i, hypothesis in enumerate(hypotheses[:self.max_workers]):
            name = f"worker-{i+1}"
            path = self.create_worktree(name, hypothesis)
            if path:
                self.apply_hypothesis(self.worktrees[-1])
        
        if not self.worktrees:
            return {'success': False, 'error': 'No worktrees created'}
        
        # Run verifications
        print("\nRunning verifications...")
        results = []
        for worktree in self.worktrees:
            print(f"  Testing {worktree['name']}...")
            result = self.run_verification(worktree, verify_cmd)
            result['hypothesis'] = worktree['hypothesis']
            results.append(result)
        
        # Select best
        best = self.select_best(results)
        
        return {
            'success': True,
            'results': results,
            'best': best,
            'worktrees': [w['path'] for w in self.worktrees]
        }
    
    def select_best(self, results: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Select the best result."""
        valid_results = [r for r in results if r.get('success') and r.get('metric') is not None]
        
        if not valid_results:
            return None
        
        # Assume lower is better for now (could be configurable)
        best = min(valid_results, key=lambda x: x['metric'])
        return best
    
    def cleanup(self) -> None:
        """Clean up worktrees."""
        print("\nCleaning up worktrees...")
        for worktree in self.worktrees:
            # Remove worktree
            self.run_git(['worktree', 'remove', '-f', worktree['path']])
            # Remove branch
            self.run_git(['branch', '-D', f"autoresearch-{worktree['name']}"])
        
        self.worktrees = []
        print("Cleanup complete")


def cmd_run(args: argparse.Namespace) -> int:
    """Run parallel experiments."""
    # Load hypotheses
    if args.hypotheses_file:
        with open(args.hypotheses_file, 'r') as f:
            data = json.load(f)
            hypotheses = data.get('hypotheses', [])
    else:
        # Default hypotheses for testing
        hypotheses = [
            {'id': 1, 'description': 'Approach A: Conservative fix'},
            {'id': 2, 'description': 'Approach B: Aggressive refactor'},
            {'id': 3, 'description': 'Approach C: Hybrid solution'}
        ]
    
    if not hypotheses:
        print("No hypotheses provided")
        return 1
    
    runner = ParallelExperiment(args.repo, args.workers)
    
    try:
        result = runner.run_parallel(hypotheses, args.verify)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("\n" + "=" * 50)
            print("Parallel Experiment Results")
            print("=" * 50)
            
            for r in result.get('results', []):
                status = "✓" if r.get('success') else "✗"
                metric = r.get('metric', 'N/A')
                print(f"{status} {r['worktree']}: metric={metric}")
            
            best = result.get('best')
            if best:
                print(f"\nBest result: {best['worktree']} with metric={best['metric']}")
        
        # Cleanup unless --keep flag
        if not args.keep:
            runner.cleanup()
        
        return 0 if result.get('success') else 1
    
    except KeyboardInterrupt:
        print("\nInterrupted, cleaning up...")
        runner.cleanup()
        return 1


def cmd_status(args: argparse.Namespace) -> int:
    """Check worktree status."""
    try:
        result = subprocess.run(
            ['git', 'worktree', 'list'],
            capture_output=True,
            text=True
        )
        print("Git Worktrees:")
        print(result.stdout)
        
        # Filter autoresearch worktrees
        lines = result.stdout.strip().split('\n')
        autoresearch_trees = [l for l in lines if 'autoresearch-worktree' in l]
        
        if autoresearch_trees:
            print(f"\nActive autoresearch worktrees: {len(autoresearch_trees)}")
        else:
            print("\nNo active autoresearch worktrees")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_cleanup(args: argparse.Namespace) -> int:
    """Clean up all autoresearch worktrees."""
    try:
        result = subprocess.run(
            ['git', 'worktree', 'list', '--porcelain'],
            capture_output=True,
            text=True
        )
        
        cleaned = 0
        for line in result.stdout.split('\n'):
            if 'worktree' in line and 'autoresearch-worktree' in line:
                path = line.split()[1]
                # Remove worktree
                subprocess.run(['git', 'worktree', 'remove', '-f', path])
                cleaned += 1
        
        # Clean up branches
        result = subprocess.run(
            ['git', 'branch'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if 'autoresearch-worker' in line:
                branch = line.strip().replace('* ', '')
                subprocess.run(['git', 'branch', '-D', branch])
        
        print(f"Cleaned up {cleaned} worktrees")
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Autoresearch Parallel Experiments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run parallel experiments
  %(prog)s run --verify "npm test -- --coverage" --workers 3

  # With hypotheses file
  %(prog)s run --verify "pytest --cov" --hypotheses hypotheses.json

  # Check status
  %(prog)s status

  # Cleanup
  %(prog)s cleanup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # run
    run_parser = subparsers.add_parser('run', help='Run parallel experiments')
    run_parser.add_argument('--verify', type=str, required=True,
                          help='Verification command')
    run_parser.add_argument('--hypotheses-file', type=str,
                          help='JSON file with hypotheses')
    run_parser.add_argument('--workers', type=int, default=3,
                          help='Number of parallel workers')
    run_parser.add_argument('--repo', type=str, default='.',
                          help='Repository path')
    run_parser.add_argument('--keep', action='store_true',
                          help='Keep worktrees after run')
    run_parser.add_argument('--json', action='store_true',
                          help='Output JSON')
    
    # status
    subparsers.add_parser('status', help='Check worktree status')
    
    # cleanup
    subparsers.add_parser('cleanup', help='Clean up worktrees')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'run': cmd_run,
        'status': cmd_status,
        'cleanup': cmd_cleanup
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
