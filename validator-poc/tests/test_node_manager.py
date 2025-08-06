"""
Unit tests for the NodeManager class.
"""
import pytest
import yaml
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from gpu_node_management import NodeManager, Node


class TestNodeManager:
    """Test cases for NodeManager class"""

    def test_initialization(self, test_logger):
        """Test NodeManager initialization"""
        etcd_url = "http://test-etcd:2380"
        manager = NodeManager(etcd_url, test_logger)

        assert manager.etcd_client.etcd_url == etcd_url
        assert manager.logger == test_logger

    def test_load_nodes_from_file_success(self, node_manager, sample_yaml_file):
        """Test successful loading of nodes from YAML file"""
        nodes = node_manager.load_nodes_from_file(sample_yaml_file)

        assert len(nodes) == 1
        assert isinstance(nodes[0], Node)
        assert nodes[0].hostname == "test-node-1"

    def test_load_nodes_from_file_not_found(self, node_manager):
        """Test loading nodes from non-existent file"""
        nodes = node_manager.load_nodes_from_file("nonexistent.yaml")

        assert nodes == []

    def test_load_nodes_from_file_invalid_yaml(self, node_manager, tmp_path):
        """Test loading nodes from invalid YAML file"""
        invalid_yaml_file = tmp_path / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("invalid: yaml: content: [")

        nodes = node_manager.load_nodes_from_file(str(invalid_yaml_file))

        assert nodes == []

    def test_put_nodes_success(self, node_manager, sample_yaml_file):
        """Test successful putting of nodes to etcd"""
        node_manager.etcd_client.put_node.return_value = True

        node_manager.put_nodes(sample_yaml_file)

        # Verify etcd_client.put_node was called
        node_manager.etcd_client.put_node.assert_called_once()

        # Verify the node passed to put_node is correct
        call_args = node_manager.etcd_client.put_node.call_args[0]
        node = call_args[0]
        assert isinstance(node, Node)
        assert node.hostname == "test-node-1"

    def test_put_nodes_failure(self, node_manager, sample_yaml_file):
        """Test putting nodes when etcd operation fails"""
        node_manager.etcd_client.put_node.return_value = False

        node_manager.put_nodes(sample_yaml_file)

        # Verify etcd_client.put_node was called despite failure
        node_manager.etcd_client.put_node.assert_called_once()

    def test_put_nodes_no_file(self, node_manager):
        """Test putting nodes when file doesn't exist"""
        node_manager.put_nodes("nonexistent.yaml")

        # Should not call etcd_client.put_node if no nodes loaded
        node_manager.etcd_client.put_node.assert_not_called()

    def test_get_node_info_success(self, node_manager, sample_node_data, capsys):
        """Test successful retrieval of node info"""
        node_manager.etcd_client.get_node.return_value = sample_node_data

        node_manager.get_node_info("test-node-1")

        # Verify etcd_client.get_node was called
        node_manager.etcd_client.get_node.assert_called_once_with("test-node-1")

        # Verify output was printed (YAML format)
        captured = capsys.readouterr()
        assert "test-node-1" in captured.out
        assert "Nvidia H200" in captured.out

    def test_get_node_info_not_found(self, node_manager):
        """Test retrieval of non-existent node info"""
        node_manager.etcd_client.get_node.return_value = None

        node_manager.get_node_info("nonexistent-node")

        # Verify etcd_client.get_node was called
        node_manager.etcd_client.get_node.assert_called_once_with("nonexistent-node")

    def test_validate_nodes_all_pass(self, node_manager, sample_yaml_file, sample_node_data):
        """Test validation when all nodes pass"""
        node_manager.etcd_client.get_node.return_value = sample_node_data

        node_manager.validate_nodes(sample_yaml_file)

        # Verify etcd_client.get_node was called
        node_manager.etcd_client.get_node.assert_called_once_with("test-node-1")

    def test_validate_nodes_conditional(self, node_manager, sample_yaml_file):
        """Test validation when nodes have missing keys (conditional)"""
        # Etcd has fewer keys than expected
        incomplete_data = {
            "hostname": "test-node-1",
            "ip": "10.0.0.10"
            # Missing other keys
        }
        node_manager.etcd_client.get_node.return_value = incomplete_data

        node_manager.validate_nodes(sample_yaml_file)

        node_manager.etcd_client.get_node.assert_called_once_with("test-node-1")

    def test_validate_nodes_fail(self, node_manager, sample_yaml_file, sample_node_data):
        """Test validation when nodes have value mismatches"""
        # Etcd has different values
        modified_data = sample_node_data.copy()
        modified_data["gpu_type"] = "Different GPU"
        modified_data["ip"] = "Different IP"

        node_manager.etcd_client.get_node.return_value = modified_data

        node_manager.validate_nodes(sample_yaml_file)

        node_manager.etcd_client.get_node.assert_called_once_with("test-node-1")

    def test_validate_nodes_not_found(self, node_manager, sample_yaml_file):
        """Test validation when node is not found in etcd"""
        node_manager.etcd_client.get_node.return_value = None

        node_manager.validate_nodes(sample_yaml_file)

        node_manager.etcd_client.get_node.assert_called_once_with("test-node-1")

    def test_validate_nodes_no_file(self, node_manager):
        """Test validation when file doesn't exist"""
        node_manager.validate_nodes("nonexistent.yaml")

        # Should not call etcd_client.get_node if no nodes loaded
        node_manager.etcd_client.get_node.assert_not_called()

    def test_validate_nodes_multiple_results(self, node_manager, tmp_path, sample_node_data):
        """Test validation with multiple nodes having different results"""
        # Create test file with multiple nodes
        nodes_data = {
            "nodes": [
                sample_node_data,  # This will pass
                {
                    "hostname": "fail-node",
                    "ip": "192.168.1.101",
                    "gpu_type": "Nvidia RTX 3090"
                },  # This will fail
                {
                    "hostname": "missing-node",
                    "ip": "192.168.1.102"
                }  # This won't be found
            ]
        }

        yaml_file = tmp_path / "multi_nodes.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(nodes_data, f)

        # Mock etcd responses
        def mock_get_node(hostname):
            if hostname == "test-node-1":
                return sample_node_data  # Pass
            elif hostname == "fail-node":
                return {"hostname": "fail-node", "ip": "192.168.1.101", "gpu_type": "Different GPU"}  # Fail
            else:
                return None  # Not found

        node_manager.etcd_client.get_node.side_effect = mock_get_node

        node_manager.validate_nodes(str(yaml_file))

        # Verify all nodes were checked
        assert node_manager.etcd_client.get_node.call_count == 3
