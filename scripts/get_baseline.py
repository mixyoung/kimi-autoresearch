#!/usr/bin/env python3
"""
Get baseline metric measurement for autoresearch.
"""
import argparse
import subprocess
import sys


def run_command(cmd: str) -> tuple[int, str]:
    """Run a shell command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def extract_number(output: str) -> float | None:
    """Try to extract a number from command output."""
    import re
    
    # Look for patterns like: 85.2%, 42, 12/34, etc.
    patterns = [
        r'(\d+\.?\d*)%',  # Percentage
        r'(\d+\.?\d*)',   # Plain number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:  # pragma: no cover (defensive)
                continue
    
    return None


def main():
    parser = argparse.ArgumentParser(description='Get baseline metric')
    parser.add_argument('--verify', type=str, required=True,
                       help='Command to run for measurement')
    parser.add_argument('--parse-number', action='store_true',
                       help='Try to extract number from output')
    
    args = parser.parse_args()
    
    print(f"Running baseline measurement...")
    print(f"Command: {args.verify}")
    
    exit_code, output = run_command(args.verify)
    
    if exit_code != 0:
        print(f"Warning: Command exited with code {exit_code}", file=sys.stderr)
    
    print(f"Output: {output.strip()}")
    
    if args.parse_number:
        number = extract_number(output)
        if number is not None:
            print(f"Extracted metric: {number}")
            return number
        else:
            print("Warning: Could not extract number from output", file=sys.stderr)
    
    return output.strip()


if __name__ == '__main__':  # pragma: no cover
    result = main()
    if isinstance(result, (int, float)):
        sys.exit(0 if result is not None else 1)
