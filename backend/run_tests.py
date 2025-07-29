#!/usr/bin/env python3
"""
Comprehensive test runner for the AI Scholar RAG system.
"""
import subprocess
import sys
import time
import argparse
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    print(f"Return code: {result.returncode}")
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # If no specific test type is selected, run all
    if not any([args.unit, args.integration, args.performance, args.e2e]):
        args.all = True
    
    success = True
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    original_dir = Path.cwd()
    
    try:
        import os
        os.chdir(backend_dir)
        
        if args.unit or args.all:
            print("\n🧪 Running Unit Tests...")
            cmd = "pytest -m unit"
            if args.verbose:
                cmd += " -v"
            if args.coverage:
                cmd += " --cov=services --cov=api --cov=core --cov=models --cov-report=html"
            success &= run_command(cmd, "Unit Tests")
        
        if args.integration or args.all:
            print("\n🔗 Running Integration Tests...")
            cmd = "pytest -m integration"
            if args.verbose:
                cmd += " -v"
            success &= run_command(cmd, "Integration Tests")
        
        if args.performance or args.all:
            print("\n⚡ Running Performance Tests...")
            cmd = "pytest -m performance"
            if args.verbose:
                cmd += " -v"
            success &= run_command(cmd, "Performance Tests")
        
        if args.e2e or args.all:
            print("\n🎯 Running End-to-End Tests...")
            cmd = "pytest -m e2e"
            if args.verbose:
                cmd += " -v"
            success &= run_command(cmd, "End-to-End Tests")
        
        # Run frontend tests if all tests are requested
        if args.all:
            print("\n🎨 Running Frontend Tests...")
            os.chdir(original_dir)
            success &= run_command("npm test -- --run", "Frontend Tests")
    
    finally:
        os.chdir(original_dir)
    
    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())