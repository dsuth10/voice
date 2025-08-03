#!/usr/bin/env python3
"""
Test runner script for Voice Dictation Assistant.
Provides easy execution of different test types and configurations.
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        return False
    else:
        print(f"\n✅ {description} completed successfully")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run tests for Voice Dictation Assistant")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "performance", "all", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--slow",
        action="store_true",
        help="Include slow tests"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Include performance tests"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add markers based on test type
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "performance":
        cmd.extend(["-m", "performance", "--runperformance"])
    elif args.type == "coverage":
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add additional options
    if args.slow:
        cmd.append("--runslow")
    
    if args.performance:
        cmd.append("--runperformance")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    if args.verbose:
        cmd.append("-v")
    
    if args.fail_fast:
        cmd.append("-x")
    
    # Add test directory
    cmd.append("tests/")
    
    # Run the tests
    success = run_command(cmd, f"{args.type.title()} Tests")
    
    if not success:
        sys.exit(1)
    
    # Generate coverage report if requested
    if args.html and args.type != "coverage":
        coverage_cmd = [
            "python", "-m", "pytest", 
            "--cov=src", 
            "--cov-report=html", 
            "--cov-report=term-missing",
            "tests/"
        ]
        run_command(coverage_cmd, "Coverage Report")
    
    print(f"\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main() 