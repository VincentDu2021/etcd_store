"""
Pytest configuration and fixtures for GPU node management tool tests.
"""
import pytest
import tempfile
import yaml
import logging
import requests
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Import the classes we want to test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils import setup_logging
from gpu_node_management import Node, EtcdClient, NodeManager


@pytest.fixture
def sample_node_data():
    """Sample node data for testing - loads from actual test data file"""
    test_data_file = Path(__file__).parent / "data" / "gpu_nodes.yaml"
    with open(test_data_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data["nodes"][0]  # Return the first node from the test data


@pytest.fixture
def sample_node(sample_node_data):
    """Sample Node object for testing"""
    return Node(sample_node_data)


@pytest.fixture
def sample_yaml_file(tmp_path, sample_node_data):
    """Create a temporary YAML file with sample node data"""
    yaml_data = {"nodes": [sample_node_data]}
    yaml_file = tmp_path / "test_nodes.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)
    return str(yaml_file)


@pytest.fixture
def mock_etcd_client():
    """Mock EtcdClient for testing"""
    mock_client = Mock(spec=EtcdClient)
    mock_client.put_node.return_value = True
    mock_client.get_node.return_value = {
        "hostname": "test-gpu-01",
        "ip": "192.168.1.100",
        "gpu_type": "Nvidia RTX 4090"
    }
    return mock_client


@pytest.fixture
def test_logger():
    """Test logger that doesn't write to files"""
    logger = logging.getLogger("test_gpu_node_manager")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Only add console handler for tests
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


@pytest.fixture
def node_manager(mock_etcd_client, test_logger):
    """NodeManager instance with mocked dependencies"""
    manager = NodeManager("http://test-etcd:2380", test_logger)
    manager.etcd_client = mock_etcd_client
    return manager


@pytest.fixture
def real_test_data_file():
    """Path to the real test data file"""
    return Path(__file__).parent / "data" / "gpu_nodes.yaml"


@pytest.fixture(scope="session")
def temp_log_file():
    """Temporary log file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        yield f.name
    # Cleanup
    os.unlink(f.name)


@pytest.fixture(scope="function", autouse=True)
def cleanup_etcd():
    """Automatically cleanup etcd data before and after each test"""
    # Setup: Clear etcd before test
    _clear_etcd_data()

    # Run the test
    yield

    # Teardown: Clear etcd after test
    _clear_etcd_data()


def _clear_etcd_data():
    """Helper function to clear all test data from etcd"""
    etcd_url = "http://localhost:2379"

    try:
        # Delete all keys with the /gpu/nodes/ prefix
        # /gpu/nodes/ base64 encoded = L2dwdS9ub2Rlcy8=
        # /gpu/nodes0 base64 encoded = L2dwdS9ub2RlczA= (range_end for prefix deletion)
        response = requests.post(
            f"{etcd_url}/v3/kv/deleterange",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "key": "L2dwdS9ub2Rlcy8=",  # base64 encoded "/gpu/nodes/"
                "range_end": "L2dwdS9ub2RlczA="  # base64 encoded "/gpu/nodes0"
            }),
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            deleted_count = result.get("deleted", 0)
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} etcd keys")

    except requests.exceptions.RequestException:
        # etcd might not be running during unit tests, which is fine
        # since unit tests use mocked etcd client
        pass


@pytest.fixture
def clean_etcd_client():
    """Real EtcdClient for integration tests with automatic cleanup"""
    client = EtcdClient("http://localhost:2379")

    # Clear before test
    _clear_etcd_data()

    yield client

    # Clear after test
    _clear_etcd_data()
