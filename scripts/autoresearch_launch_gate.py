#!/usr/bin/env python3
"""
Launch gate for autoresearch.
Decides whether to start fresh, resume, or block.
"""
import argparse
import json
import os

STATE_FILE = "autoresearch-state.json"
RESULTS_FILE = "autoresearch-results.tsv"


def check_existing_state() -> dict:
    """Check for existing state to resume from."""
    if not os.path.exists(STATE_FILE):
        return {'can_resume': False, 'reason': 'No state file found'}
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        status = state.get('status', '')
        
        if status == 'completed':
            return {'can_resume': False, 'reason': 'Previous run completed'}
        elif status == 'interrupted':
            return {
                'can_resume': True,
                'mode': 'full_resume',
                'reason': 'Previous run was interrupted',
                'state': state
            }
        elif status == 'running':
            return {
                'can_resume': True,
                'mode': 'mini_wizard',
                'reason': 'Previous run may still be active',
                'state': state
            }
        else:
            return {
                'can_resume': True,
                'mode': 'fallback',
                'reason': 'Unknown status, check state',
                'state': state
            }
    
    except json.JSONDecodeError:
        return {'can_resume': False, 'reason': 'State file corrupted'}


def check_results_consistency() -> dict:
    """Cross-check results file with state."""
    if not os.path.exists(RESULTS_FILE):
        return {'consistent': True, 'results_count': 0}
    
    if not os.path.exists(STATE_FILE):
        return {'consistent': True, 'results_count': 0, 'note': 'No state file'}
    
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        with open(RESULTS_FILE, 'r') as f:
            import csv
            reader = csv.DictReader(f, delimiter='\t')
            results = list(reader)
        
        state_iteration = state.get('iteration', 0)
        results_count = len(results)
        
        # Results should have baseline + iterations
        expected = state_iteration + 1
        
        if results_count == expected:
            return {
                'consistent': True,
                'results_count': results_count,
                'state_iteration': state_iteration
            }
        else:
            return {
                'consistent': False,
                'results_count': results_count,
                'state_iteration': state_iteration,
                'expected': expected,
                'note': f'Mismatch: {results_count} results vs {expected} expected'
            }
    
    except Exception as e:
        return {'consistent': False, 'error': str(e)}


def decide_launch_action(args) -> dict:
    """Decide whether to launch, resume, or block."""
    
    # Check for force flags
    if args.force_fresh:
        return {
            'action': 'fresh',
            'reason': 'Force fresh start requested'
        }
    
    if args.force_resume:
        state_check = check_existing_state()
        if state_check['can_resume']:
            return {
                'action': 'resume',
                'mode': state_check.get('mode', 'full_resume'),
                'reason': 'Force resume requested',
                'state': state_check.get('state')
            }
        else:
            return {
                'action': 'block',
                'reason': f'Cannot resume: {state_check["reason"]}'
            }
    
    # Check existing state
    state_check = check_existing_state()
    
    if state_check['can_resume']:
        # Check consistency
        consistency = check_results_consistency()
        
        if consistency.get('consistent', False):
            return {
                'action': 'resume',
                'mode': state_check.get('mode', 'full_resume'),
                'reason': state_check['reason'],
                'state': state_check.get('state')
            }
        else:
            return {
                'action': 'needs_confirmation',
                'mode': 'mini_wizard',
                'reason': f'{state_check["reason"]} - {consistency.get("note", "")}',
                'state': state_check.get('state')
            }
    
    # No existing state, fresh start
    return {
        'action': 'fresh',
        'reason': state_check['reason']
    }


def main():
    parser = argparse.ArgumentParser(description='Autoresearch launch gate')
    parser.add_argument('--force-fresh', action='store_true',
                       help='Force a fresh start')
    parser.add_argument('--force-resume', action='store_true',
                       help='Force resume of existing run')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check, do not decide')
    parser.add_argument('--format', type=str, default='json',
                       choices=['json', 'text'])
    
    args = parser.parse_args()
    
    if args.check_only:
        state_check = check_existing_state()
        consistency = check_results_consistency()
        
        result = {
            'state': state_check,
            'consistency': consistency
        }
        
        if args.format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("Launch Gate Check")
            print("=" * 40)
            print(f"Can resume: {state_check['can_resume']}")
            print(f"Reason: {state_check['reason']}")
            if 'state' in state_check:
                print(f"Status: {state_check['state'].get('status', 'unknown')}")
            print(f"Results consistent: {consistency.get('consistent', False)}")
    
    else:
        decision = decide_launch_action(args)
        
        if args.format == 'json':
            print(json.dumps(decision, indent=2))
        else:
            print("Launch Decision")
            print("=" * 40)
            print(f"Action: {decision['action']}")
            print(f"Reason: {decision['reason']}")
            if 'mode' in decision:
                print(f"Mode: {decision['mode']}")
        
        # Exit codes
        if decision['action'] == 'block':
            exit(1)
        elif decision['action'] == 'needs_confirmation':
            exit(2)
        else:
            exit(0)


if __name__ == '__main__':
    main()
