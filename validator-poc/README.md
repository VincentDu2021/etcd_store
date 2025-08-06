# GPU Node Management Tool

A Python tool for managing GPU node configurations in etcd with comprehensive logging and validation capabilities.

## Features

- **Clean architecture** with separated business logic and utilities
- **Object-oriented design** with Node, EtcdClient, and NodeManager classes
- **Three main operations**: Put (update), Get (retrieve), Validate (compare)
- **Comprehensive logging** with configurable levels and file output
- **YAML-based configuration** for easy node specification
- **Robust error handling** and validation
- **Extensive test coverage** (98% with 51 test cases)
- **Real GPU data integration** with Nvidia H200 specifications
- **Automated etcd setup** with Docker support and cleanup utilities

## Project Structure

```
├── node_validator.py          # Main CLI application
├── gpu_node_management/       # Core business logic package
│   ├── __init__.py           # Package exports
│   ├── node.py               # Node class definition
│   ├── etcd_client.py        # etcd client operations
│   └── node_manager.py       # High-level node management
├── utils/                     # Utility functions and tools
│   ├── __init__.py           # Package exports
│   ├── logging.py            # Logging configuration
│   └── setup_etcd.sh         # etcd setup and management script
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Pytest configuration
├── ARCHITECTURE.md           # Detailed architecture documentation
├── README.md                 # This file
└── tests/
    ├── conftest.py           # Pytest fixtures
    ├── data/
    │   └── gpu_nodes.yaml    # Test data with real GPU specs
    ├── test_node.py          # Node class tests
    ├── test_etcd_client.py   # EtcdClient tests
    ├── test_node_manager.py  # NodeManager tests
    └── test_integration.py   # Integration tests
```

## Installation

1. **Clone or download the project**

2. **Set up a Python virtual environment** (recommended):
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source .venv/bin/activate
   
   # On Windows:
   # .venv\Scripts\activate
   ```
   
   When activated, your prompt should show `(.venv)` indicating the virtual environment is active.

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Dependencies include:
   - `pyyaml==6.0.1` - YAML parsing
   - `requests==2.32.4` - HTTP client for etcd
   - `pytest==7.4.4` - Testing framework
   - `pytest-mock==3.12.0` - Enhanced mocking
   - `pytest-cov==4.1.0` - Coverage reporting

## Setting Up Local etcd (for Integration Testing)

### Option 1: Using the Setup Script (Recommended)

The project includes an automated setup script that handles Docker installation detection and etcd management:

```bash
# Make script executable
chmod +x utils/setup_etcd.sh

# Show help and available commands
./utils/setup_etcd.sh help

# Start etcd server
./utils/setup_etcd.sh start

# Check etcd status
./utils/setup_etcd.sh status

# Clean etcd data (useful for testing)
./utils/setup_etcd.sh clean

# Stop etcd server
./utils/setup_etcd.sh stop
```

The script automatically:
- Detects if Docker requires sudo
- Manages etcd container lifecycle
- Provides status checking and data cleanup
- Uses etcd v3.5.9 with proper configuration

### Option 2: Manual Docker Setup

1. **Install Docker** if not already installed

2. **Run etcd container**:
   ```bash
   docker run -d \
     --name etcd-server \
     -p 2379:2379 \
     -p 2380:2380 \
     quay.io/coreos/etcd:v3.5.9 \
     /usr/local/bin/etcd \
     --name s1 \
     --data-dir /etcd-data \
     --listen-client-urls http://0.0.0.0:2379 \
     --advertise-client-urls http://0.0.0.0:2379 \
     --listen-peer-urls http://0.0.0.0:2380 \
     --initial-advertise-peer-urls http://0.0.0.0:2380 \
     --initial-cluster s1=http://0.0.0.0:2380 \
     --initial-cluster-token tkn \
     --initial-cluster-state new \
     --log-level info \
     --logger zap \
     --log-outputs stderr
   ```

3. **Verify etcd is running**:
   ```bash
   # Check container status
   docker ps | grep etcd-server

   # Test etcd connection
   curl http://localhost:2379/version
   ```

4. **Stop etcd when done**:
   ```bash
   docker stop etcd-server
   docker rm etcd-server
   ```

### Option 3: Install etcd Natively

1. **Download etcd** (Linux):
   ```bash
   ETCD_VER=v3.5.9
   GITHUB_URL=https://github.com/etcd-io/etcd/releases/download
   DOWNLOAD_URL=${GITHUB_URL}/${ETCD_VER}/etcd-${ETCD_VER}-linux-amd64.tar.gz

   curl -L ${DOWNLOAD_URL} -o etcd-${ETCD_VER}-linux-amd64.tar.gz
   tar xzvf etcd-${ETCD_VER}-linux-amd64.tar.gz
   cd etcd-${ETCD_VER}-linux-amd64
   ```

2. **Start etcd**:
   ```bash
   ./etcd --name s1 \
     --data-dir /tmp/etcd-data \
     --listen-client-urls http://0.0.0.0:2379 \
     --advertise-client-urls http://0.0.0.0:2379 \
     --listen-peer-urls http://0.0.0.0:2380 \
     --initial-advertise-peer-urls http://0.0.0.0:2380 \
     --initial-cluster s1=http://0.0.0.0:2380 \
     --initial-cluster-token tkn \
     --initial-cluster-state new
   ```

## Running Tests

### Quick Test Run

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=node_validator --cov-report=term-missing
```

### Test Categories

```bash
# Run only unit tests
pytest tests/test_node.py tests/test_etcd_client.py tests/test_node_manager.py

# Run only integration tests
pytest tests/test_integration.py

# Run specific test class
pytest tests/test_node.py::TestNode

# Run specific test method
pytest tests/test_node.py::TestNode::test_node_initialization
```

### Test Configuration

The project uses `pyproject.toml` for pytest configuration:
- **Test discovery**: Automatically finds `test_*.py` files
- **Live logging**: Shows logs during test execution
- **Markers**: Supports `unit`, `integration`, and `etcd` markers
- **Coverage**: Integrated coverage reporting

### Understanding Test Output

**Example successful test run**:
```
============================== test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.4, pluggy-1.6.0
rootdir: /home/dev/vdu/source/gpu-metal-automation/poc
configfile: pyproject.toml
plugins: mock-3.12.0, cov-4.1.0
collecting ... collected 51 items

tests/test_node.py::TestNode::test_node_initialization PASSED     [ 2%]
tests/test_etcd_client.py::TestEtcdClient::test_initialization PASSED [ 4%]
...
============================== 51 passed in 0.34s ===============================

---------- coverage: platform linux, python 3.10.12-final-0 ----------
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
node_validator.py     183      4    98%   278-280, 284
-------------------------------------------------
TOTAL                 183      4    98%
```

## Using the Application

### Basic Usage

```bash
# Show help
python node_validator.py --help

# Put (update) nodes from YAML file
python node_validator.py put --file tests/data/gpu_nodes.yaml

# Get node information
python node_validator.py get --hostname gpu-node-01

# Validate nodes against etcd
python node_validator.py validate --file tests/data/gpu_nodes.yaml
```

### Advanced Usage

```bash
# Custom etcd URL
python node_validator.py --etcd http://localhost:2379 put --file tests/data/gpu_nodes.yaml

# Custom logging
python node_validator.py --log-file custom.log --log-level DEBUG get --hostname gpu-node-01

# Full example with all options
python node_validator.py \
  --etcd http://localhost:2379 \
  --log-file operations.log \
  --log-level INFO \
  validate --file tests/data/gpu_nodes.yaml
```

### Sample Node Configuration

The `tests/data/gpu_nodes.yaml` file contains real GPU hardware specifications:

```yaml
nodes:
  - hostname: "atl1g1r11bm2"
    ip: "10.46.64.131"
    gpu_type: "Nvidia H200"
    bios_version: "2.4.4"
    nvidia_driver: "575.148.08"
    cuda_version: "12.8"
    os: "ubuntu-22.04"
    kernel: "6.8.0-60-generic"
    secure_boot: false
    monitoring_enabled: false
    tags: ["available", "H200"]
```

## Architecture

The codebase uses a modular architecture with clear separation of concerns:

### Core Components

- **`gpu_node_management/node.py`**: Node class representing GPU hardware specifications
- **`gpu_node_management/etcd_client.py`**: Low-level etcd operations with base64 encoding
- **`gpu_node_management/node_manager.py`**: High-level business logic for node management
- **`utils/logging.py`**: Centralized logging configuration utilities
- **`utils/setup_etcd.sh`**: etcd setup and management script
- **`node_validator.py`**: Main CLI interface and argument parsing

### Import Structure

```python
# Main application
from utils import setup_logging
from gpu_node_management import NodeManager

# Individual components (for testing)
from utils import setup_logging
from gpu_node_management import Node, EtcdClient, NodeManager
```

For detailed architecture information, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

### Benefits of Modular Design

1. **Maintainability**: Each component has a single responsibility
2. **Testability**: Classes can be tested in isolation
3. **Reusability**: Components can be imported independently
4. **Scalability**: Easy to add new features or modify existing ones
5. **Clarity**: Clear separation between CLI, business logic, and data access

## Testing with Real etcd vs Mocked

### Mocked Tests (Default)
Most tests use mocked etcd connections for:
- **Fast execution** - No network dependencies
- **Reliable results** - Consistent behavior
- **Isolation** - Tests don't interfere with each other

### Integration Tests with Real etcd
To test against a real etcd instance:

1. **Start etcd** using the setup script:
   ```bash
   ./utils/setup_etcd.sh start
   ```

2. **Run integration tests**:
   ```bash
   # Test all operations with real etcd
   python node_validator.py --etcd http://localhost:2379 put --file tests/data/gpu_nodes.yaml
   python node_validator.py --etcd http://localhost:2379 get --hostname atl1g1r11bm2
   python node_validator.py --etcd http://localhost:2379 validate --file tests/data/gpu_nodes.yaml
   ```

3. **Clean up test data**:
   ```bash
   ./utils/setup_etcd.sh clean
   ```

## Troubleshooting

### Common Issues

1. **Import errors**:
   ```bash
   # Ensure you're in the correct directory
   cd /path/to/gpu-metal-automation/poc
   # Ensure dependencies are installed
   pip install -r requirements.txt
   ```

2. **etcd connection failures**:
   ```bash
   # Check if etcd is running
   curl http://localhost:2379/version
   # Check if ports are available
   netstat -lan | grep 2379
   ```

3. **Test failures**:
   ```bash
   # Run with more verbose output
   pytest tests/ -v -s
   # Run individual failing test
   pytest tests/test_specific.py::TestClass::test_method -v
   ```

4. **Permission issues**:
   ```bash
   # Make sure log directory is writable
   mkdir -p logs
   chmod 755 logs
   ```

### Debug Mode

For troubleshooting, run with debug logging:
```bash
python node_validator.py --log-level DEBUG <command>
```

This will show detailed information about:
- HTTP requests to etcd
- YAML parsing
- Node comparison details
- Error stack traces

## Development

### Adding New Tests

1. **Unit tests**: Add to appropriate `test_*.py` file
2. **Integration tests**: Add to `test_integration.py`
3. **Test data**: Add to `tests/data/` directory
4. **Fixtures**: Add to `tests/conftest.py`

### Running Specific Test Types

```bash
# Only fast unit tests
pytest tests/test_node.py tests/test_etcd_client.py tests/test_node_manager.py

# Only integration tests
pytest tests/test_integration.py

# Tests requiring etcd (if you add the marker)
pytest tests/ -m "etcd"
```

### Coverage Analysis

```bash
# Generate detailed coverage report
pytest tests/ --cov=node_validator --cov-report=html

# Open coverage report in browser
open htmlcov/index.html
```

This will show exactly which lines are covered by tests and which need attention.
