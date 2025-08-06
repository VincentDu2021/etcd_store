#!/bin/bash

# GPU Node Validator Test Runner
# This script runs the complete test suite with various options

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run tests with given parameters
run_tests() {
    local test_type="$1"
    local pytest_args="$2"

    print_status "Running $test_type tests..."
    echo "Command: python -m pytest $pytest_args"
    echo "----------------------------------------"

    if python -m pytest $pytest_args; then
        print_success "$test_type tests completed successfully"
    else
        print_error "$test_type tests failed"
        return 1
    fi
    echo
}

# Change to the validator-poc directory (parent of tests/)
cd "$(dirname "$0")/.."

print_status "GPU Node Validator Test Suite"
print_status "Working directory: $(pwd)"
echo

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    print_error "requirements.txt not found. Please run this script from the validator-poc directory or tests/ subdirectory."
    exit 1
fi

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install requirements: pip install -r requirements.txt"
    exit 1
fi

# Default test run
if [[ $# -eq 0 ]]; then
    print_status "Running default test suite (verbose with coverage)"
    run_tests "Default" "tests/ -v --cov=gpu_node_management --cov-report=term-missing"
    exit 0
fi

# Parse command line arguments
case "$1" in
    "basic"|"simple")
        run_tests "Basic" "tests/ -v"
        ;;
    "coverage"|"cov")
        run_tests "Coverage" "tests/ --cov=gpu_node_management --cov-report=term-missing"
        ;;
    "verbose"|"v")
        run_tests "Verbose" "tests/ -v --tb=short"
        ;;
    "quiet"|"q")
        run_tests "Quiet" "tests/ -q"
        ;;
    "integration"|"int")
        run_tests "Integration" "tests/test_integration.py -v"
        ;;
    "unit")
        run_tests "Unit" "tests/test_node.py tests/test_node_manager.py tests/test_etcd_client.py -v"
        ;;
    "fast")
        run_tests "Fast" "tests/ -x -q"
        ;;
    "full")
        print_status "Running comprehensive test suite"
        run_tests "Basic" "tests/ -v" && \
        run_tests "Coverage" "tests/ --cov=gpu_node_management --cov-report=term-missing" && \
        run_tests "Integration" "tests/test_integration.py -v"
        ;;
    "help"|"-h"|"--help")
        echo "GPU Node Validator Test Runner"
        echo
        echo "Usage: $0 [TEST_TYPE]"
        echo
        echo "Available test types:"
        echo "  basic, simple    - Run tests with verbose output"
        echo "  coverage, cov    - Run tests with coverage reporting"
        echo "  verbose, v       - Run tests with verbose output and short traceback"
        echo "  quiet, q         - Run tests quietly"
        echo "  integration, int - Run only integration tests"
        echo "  unit            - Run only unit tests"
        echo "  fast            - Run tests quickly (stop on first failure)"
        echo "  full            - Run comprehensive test suite"
        echo "  help            - Show this help message"
        echo
        echo "Default (no arguments): Run verbose tests with coverage"
        echo
        echo "Examples:"
        echo "  $0                # Default test run"
        echo "  $0 basic          # Basic verbose tests"
        echo "  $0 coverage       # Tests with coverage report"
        echo "  $0 fast           # Quick test run"
        echo "  $0 full           # Comprehensive test suite"
        ;;
    *)
        print_error "Unknown test type: $1"
        print_warning "Run '$0 help' to see available options"
        exit 1
        ;;
esac
