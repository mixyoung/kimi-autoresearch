#!/usr/bin/env python3
"""
Main entry point for kimi-autoresearch.
Orchestrates the entire autoresearch workflow.
"""
import argparse
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import i18n support
sys.path.insert(0, SCRIPT_DIR)
from autoresearch_i18n import _, init_locale, set_locale, get_locale_name


def run_script(name: str, args: list[str]) -> tuple[int, str]:
    """Run a helper script."""
    script_path = os.path.join(SCRIPT_DIR, name)
    cmd = ['python', script_path] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "Script timed out"
    except Exception as e:
        return -1, str(e)


def cmd_init(args):
    """Initialize a new run."""
    script_args = [
        '--goal', args.goal,
        '--metric', args.metric,
        '--verify', args.verify,
        '--direction', args.direction,
        '--mode', args.mode
    ]
    
    if args.scope:
        script_args.extend(['--scope', args.scope])
    if args.guard:
        script_args.extend(['--guard', args.guard])
    if args.iterations:
        script_args.extend(['--iterations', str(args.iterations)])
    
    code, output = run_script('autoresearch_init_run.py', script_args)
    print(output)
    return code


def cmd_health(args):
    """Run health check."""
    script_args = []
    if args.json:
        script_args.append('--format=json')
    if args.fail_on_warn:
        script_args.append('--fail-on-warn')
    
    code, output = run_script('autoresearch_health_check.py', script_args)
    print(output)
    return code


def cmd_launch_gate(args):
    """Check if we should resume or start fresh."""
    script_args = []
    if args.force_fresh:
        script_args.append('--force-fresh')
    if args.force_resume:
        script_args.append('--force-resume')
    if args.json:
        script_args.append('--format=json')
    
    code, output = run_script('autoresearch_launch_gate.py', script_args)
    print(output)
    return code


def cmd_decide(args):
    """Make a keep/discard decision."""
    script_args = [
        '--action', 'decide',
        '--current', str(args.current),
        '--baseline', str(args.baseline),
        '--direction', args.direction,
        '--guard-passed', str(args.guard_passed)
    ]
    
    code, output = run_script('autoresearch_decision.py', script_args)
    print(output)
    return code


def cmd_baseline(args):
    """Get baseline measurement."""
    script_args = ['--verify', args.verify]
    if args.parse_number:
        script_args.append('--parse-number')
    
    code, output = run_script('get_baseline.py', script_args)
    print(output)
    return code


def cmd_git(args):
    """Git operations."""
    script_args = ['--action', args.git_action]
    if args.message:
        script_args.extend(['--message', args.message])
    
    code, output = run_script('check_git.py', script_args)
    print(output)
    return code


def cmd_log(args):
    """Log a result."""
    script_args = [
        '--iteration', str(args.iteration),
        '--commit', args.commit,
        '--metric', str(args.metric),
        '--status', args.status,
        '--description', args.description
    ]
    if args.delta:
        script_args.extend(['--delta', args.delta])
    
    code, output = run_script('log_result.py', script_args)
    print(output)
    return code


def cmd_report(args):
    """Generate report."""
    code, output = run_script('generate_report.py', [])
    print(output)
    return code


def cmd_lang(args):
    """Handle language command."""
    if args.locale:
        if set_locale(args.locale):
            print(f"Language switched to: {get_locale_name(args.locale)}")
        return 0
    else:
        print(f"Current language: {get_locale_name(getattr(sys.modules[__name__], '_current_locale', 'zh'))}")
        return 0


def cmd_search(args):
    """Web search when stuck."""
    script_args = []
    
    if args.subcommand == 'check':
        script_args.append('check')
        if args.state_file:
            script_args.extend(['--state-file', args.state_file])
        if args.force:
            script_args.append('--force')
    elif args.subcommand == 'query':
        script_args.extend(['search'])
        if args.goal:
            script_args.extend(['--goal', args.goal])
        if args.error:
            script_args.extend(['--error', args.error])
        if args.strategy:
            script_args.extend(['--strategy', args.strategy])
    
    if args.json:
        script_args.append('--json')
    
    code, output = run_script('autoresearch_web_search.py', script_args)
    print(output)
    return code


def main():
    parser = argparse.ArgumentParser(
        description='Kimi Autoresearch - Main orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a run
  %(prog)s init --goal "Reduce type errors" --metric "error count" --verify "tsc --noEmit 2>&1 | grep -c error"

  # Health check
  %(prog)s health

  # Check launch gate
  %(prog)s launch-gate

  # Get baseline
  %(prog)s baseline --verify "npm test -- --coverage | grep 'All files'"

  # Make decision
  %(prog)s decide --current 42 --baseline 47 --direction lower --guard-passed true

  # Git operations
  %(prog)s git --action commit --message "experiment: fix types"

  # Log result
  %(prog)s log --iteration 1 --commit abc123 --metric 42 --status keep --description "Fixed auth types"

  # Generate report
  %(prog)s report
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize a new run')
    init_parser.add_argument('--goal', type=str, required=True)
    init_parser.add_argument('--metric', type=str, required=True)
    init_parser.add_argument('--verify', type=str, required=True)
    init_parser.add_argument('--scope', type=str, default='')
    init_parser.add_argument('--guard', type=str, default='')
    init_parser.add_argument('--direction', type=str, default='lower',
                           choices=['higher', 'lower'])
    init_parser.add_argument('--iterations', type=int, default=0)
    init_parser.add_argument('--mode', type=str, default='loop',
                           choices=['loop', 'debug', 'fix', 'security', 'ship'])
    
    # health command
    health_parser = subparsers.add_parser('health', help='Run health check')
    health_parser.add_argument('--json', action='store_true')
    health_parser.add_argument('--fail-on-warn', action='store_true')
    
    # launch-gate command
    gate_parser = subparsers.add_parser('launch-gate', help='Check launch gate')
    gate_parser.add_argument('--force-fresh', action='store_true')
    gate_parser.add_argument('--force-resume', action='store_true')
    gate_parser.add_argument('--json', action='store_true')
    
    # decide command
    decide_parser = subparsers.add_parser('decide', help='Make keep/discard decision')
    decide_parser.add_argument('--current', type=float, required=True)
    decide_parser.add_argument('--baseline', type=float, required=True)
    decide_parser.add_argument('--direction', type=str, required=True,
                             choices=['higher', 'lower'])
    decide_parser.add_argument('--guard-passed', type=bool, default=True)
    
    # baseline command
    baseline_parser = subparsers.add_parser('baseline', help='Get baseline metric')
    baseline_parser.add_argument('--verify', type=str, required=True)
    baseline_parser.add_argument('--parse-number', action='store_true')
    
    # git command
    git_parser = subparsers.add_parser('git', help='Git operations')
    git_parser.add_argument('--action', type=str, required=True,
                          choices=['check', 'commit', 'revert', 'stash', 'commit-hash'])
    git_parser.add_argument('--message', type=str, default='autoresearch: iteration')
    
    # log command
    log_parser = subparsers.add_parser('log', help='Log a result')
    log_parser.add_argument('--iteration', type=int, required=True)
    log_parser.add_argument('--commit', type=str, required=True)
    log_parser.add_argument('--metric', type=str, required=True)
    log_parser.add_argument('--delta', type=str, default='0')
    log_parser.add_argument('--status', type=str, required=True,
                          choices=['baseline', 'keep', 'discard', 'crash'])
    log_parser.add_argument('--description', type=str, required=True)
    
    # report command
    subparsers.add_parser('report', help='Generate report')
    
    # lang command
    lang_parser = subparsers.add_parser('lang', help='Language settings')
    lang_parser.add_argument('locale', nargs='?', help='Locale code (en/zh)')
    
    # search command
    search_parser = subparsers.add_parser('search', help='Web search when stuck')
    search_subparsers = search_parser.add_subparsers(dest='subcommand')
    
    search_check = search_subparsers.add_parser('check', help='Check if stuck and search')
    search_check.add_argument('--state-file', type=str, help='State file path')
    search_check.add_argument('--force', action='store_true', help='Force search')
    
    search_query = search_subparsers.add_parser('query', help='Manual search query')
    search_query.add_argument('--goal', type=str, help='Current goal')
    search_query.add_argument('--error', type=str, help='Error message')
    search_query.add_argument('--strategy', type=str, help='Current strategy')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    commands = {
        'init': cmd_init,
        'health': cmd_health,
        'launch-gate': cmd_launch_gate,
        'decide': cmd_decide,
        'baseline': cmd_baseline,
        'git': cmd_git,
        'log': cmd_log,
        'report': cmd_report,
        'lang': cmd_lang,
        'search': cmd_search
    }
    
    # Initialize i18n
    init_locale()
    
    code = commands[args.command](args)
    sys.exit(code)


if __name__ == '__main__':
    main()
