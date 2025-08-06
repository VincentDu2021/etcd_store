"""
Integration tests for the GPU node management tool.
These tests use the real test data and test the integration between components.
"""
import base64
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, Mock

from utils import setup_logging
from gpu_node_management import NodeManager
from node_validator import main


class TestIntegration:
    """Integration test cases"""

    def test_setup_logging_creates_logger(self, temp_log_file):
        """Test that setup_logging creates a properly configured logger"""
        logger = setup_logging(temp_log_file, "DEBUG")

        assert logger.name == "gpu_node_manager"
        assert logger.level == 10  # DEBUG level
        assert len(logger.handlers) == 2  # File and console handlers

    def test_setup_logging_different_levels(self, temp_log_file):
        """Test setup_logging with different log levels"""
        for level_name, level_value in [
            ("DEBUG", 10), ("INFO", 20), ("WARNING", 30), ("ERROR", 40), ("CRITICAL", 50)
        ]:
            logger = setup_logging(temp_log_file, level_name)
            assert logger.level == level_value

    @patch('sys.argv', ['node_validator.py', '--help'])
    def test_main_help_command(self):
        """Test main function with help command"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # Help command should exit with code 0
        assert exc_info.value.code == 0

    @patch('sys.argv', ['node_validator.py'])
    def test_main_no_action(self):
        """Test main function with no action specified"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        # No action should exit with code 1
        assert exc_info.value.code == 1

    @patch('requests.post')
    @patch('sys.argv', ['node_validator.py', 'put', '--file', 'tests/data/gpu_nodes.yaml'])
    def test_main_put_command_integration(self, mock_requests, real_test_data_file):
        """Test main function with put command using real test data"""
        # Mock successful etcd response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response

        # This should not raise an exception
        try:
            main()
        except SystemExit as e:
            # Should exit with 0 for success
            assert e.code != 1

    @patch('requests.post')
    @patch('sys.argv', ['node_validator.py', 'get', '--hostname', 'gpu-node-01'])
    def test_main_get_command_integration(self, mock_requests):
        """Test main function with get command"""
        # Mock successful etcd response for get
        test_data = {"hostname": "gpu-node-01", "gpu_type": "Nvidia A100"}
        yaml_data = yaml.dump(test_data)
        encoded_value = base64.b64encode(yaml_data.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "kvs": [{"value": encoded_value}]
        }
        mock_requests.return_value = mock_response

        try:
            main()
        except SystemExit as e:
            assert e.code != 1

    @patch('requests.post')
    @patch('sys.argv', ['node_validator.py', 'validate', '--file', 'tests/data/gpu_nodes.yaml'])
    def test_main_validate_command_integration(self, mock_requests, real_test_data_file):
        """Test main function with validate command using real test data"""
        # Mock successful etcd response for validate
        # Read the real test data to mock the etcd response
        with open(real_test_data_file) as f:
            test_yaml_data = yaml.safe_load(f)

        node_data = test_yaml_data["nodes"][0]  # Get first node
        yaml_data = yaml.dump(node_data)
        encoded_value = base64.b64encode(yaml_data.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "kvs": [{"value": encoded_value}]
        }
        mock_requests.return_value = mock_response

        try:
            main()
        except SystemExit as e:
            assert e.code != 1

    def test_real_test_data_file_exists(self, real_test_data_file):
        """Test that the real test data file exists and is valid"""
        assert real_test_data_file.exists()

        with open(real_test_data_file) as f:
            data = yaml.safe_load(f)

        assert "nodes" in data
        assert len(data["nodes"]) > 0

        # Verify first node has required fields
        node = data["nodes"][0]
        assert "hostname" in node
        assert "gpu_type" in node

    @patch('requests.post')
    def test_end_to_end_workflow(self, mock_requests, real_test_data_file, temp_log_file):
        """Test complete workflow: put -> get -> validate"""
        # Read real test data
        with open(real_test_data_file) as f:
            test_data = yaml.safe_load(f)
        node_data = test_data["nodes"][0]

        # Mock etcd responses
        def mock_etcd_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200

            # For put operations, just return success
            if "/v3/kv/put" in args[0]:
                return mock_response

            # For get/range operations, return the node data
            elif "/v3/kv/range" in args[0]:
                yaml_data = yaml.dump(node_data)
                encoded_value = base64.b64encode(yaml_data.encode()).decode()
                mock_response.json.return_value = {
                    "kvs": [{"value": encoded_value}]
                }
                return mock_response

            return mock_response

        mock_requests.side_effect = mock_etcd_response

        # Setup logger and node manager
        logger = setup_logging(temp_log_file, "INFO")
        manager = NodeManager("http://test-etcd:2380", logger)

        # Test put operation
        manager.put_nodes(str(real_test_data_file))

        # Test get operation
        manager.get_node_info(node_data["hostname"])

        # Test validate operation
        manager.validate_nodes(str(real_test_data_file))

        # Verify etcd was called multiple times
        assert mock_requests.call_count >= 3
