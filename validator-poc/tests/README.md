# Test Runner Script

This directory contains the test runner script for the GPU Node Validator project.

## Usage

The `run_tests.sh` script provides multiple testing options:

```bash
# Run from validator-poc directory
./tests/run_tests.sh [TEST_TYPE]

# Or from tests directory
cd tests && ./run_tests.sh [TEST_TYPE]
```

## Available Test Types

| Command | Description |
|---------|-------------|
| `basic`, `simple` | Run tests with verbose output |
| `coverage`, `cov` | Run tests with coverage reporting |
| `verbose`, `v` | Run tests with verbose output and short traceback |
| `quiet`, `q` | Run tests quietly |
| `integration`, `int` | Run only integration tests |
| `unit` | Run only unit tests |
| `fast` | Run tests quickly (stop on first failure) |
| `full` | Run comprehensive test suite |
| `help` | Show help message |

**Default (no arguments)**: Run verbose tests with coverage

## Examples

```bash
# Default test run with coverage
./tests/run_tests.sh

# Quick basic test
./tests/run_tests.sh basic

# Coverage report
./tests/run_tests.sh coverage

# Fast test run (stops on first failure)
./tests/run_tests.sh fast

# Comprehensive test suite
./tests/run_tests.sh full

# Only integration tests
./tests/run_tests.sh integration

# Only unit tests
./tests/run_tests.sh unit
```

## Features

- **Colored Output**: Success, error, and info messages are color-coded
- **Error Handling**: Script exits on test failures with appropriate error codes
- **Smart Directory Detection**: Works from both validator-poc and tests directories
- **Prerequisite Checking**: Validates pytest availability and requirements.txt presence
- **Multiple Test Modes**: Supports various pytest configurations for different use cases

## Requirements

- Python 3.7+
- pytest and other dependencies from `requirements.txt`
- Bash shell

The script automatically checks for prerequisites and provides helpful error messages if they're missing.
