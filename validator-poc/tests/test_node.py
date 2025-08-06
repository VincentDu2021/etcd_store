"""
Unit tests for the Node class.
These tests validate the initialization, default values,
data serialization, and comparison methods of the Node class.
"""
import pytest
import yaml
from gpu_node_management import Node


class TestNode:
    """Test cases for Node class"""

    def test_node_initialization(self, sample_node_data):
        """Test Node initialization with valid data"""
        node = Node(sample_node_data)

        assert node.hostname == "test-node-1"
        assert node.ip == "10.0.0.10"
        assert node.gpu_type == "Nvidia H200"
        assert node.bios_version == "2.4.4"
        assert node.nvidia_driver == "575.148.08"
        assert node.cuda_version == 12.8
        assert node.os == "ubuntu-22.04"
        assert node.kernel == "6.8.0-60-generic"
        assert node.secure_boot is False
        assert node.monitoring_enabled is False
        assert node.tags == ["available", "H200"]

    def test_node_initialization_with_defaults(self):
        """Test Node initialization with minimal data uses defaults"""
        minimal_data = {"hostname": "minimal-node"}
        node = Node(minimal_data)

        assert node.hostname == "minimal-node"
        assert node.ip == ""
        assert node.gpu_type == ""
        assert node.secure_boot is False
        assert node.monitoring_enabled is False
        assert node.tags == []

    def test_to_dict(self, sample_node, sample_node_data):
        """Test to_dict method returns original data"""
        result = sample_node.to_dict()
        assert result == sample_node_data

    def test_to_yaml(self, sample_node, sample_node_data):
        """Test to_yaml method produces valid YAML"""
        yaml_output = sample_node.to_yaml()

        # Parse the YAML back to verify it's valid
        parsed_data = yaml.safe_load(yaml_output)
        assert parsed_data == sample_node_data

    def test_compare_with_identical_data(self, sample_node, sample_node_data):
        """Test comparison with identical data returns PASS"""
        result = sample_node.compare_with(sample_node_data)

        assert result["status"] == "PASS"
        assert result["extra_keys"] == []
        assert result["value_mismatches"] == []

    def test_compare_with_missing_keys(self, sample_node):
        """Test comparison with missing keys returns CONDITIONAL"""
        incomplete_data = {
            "hostname": "test-gpu-01",
            "ip": "192.168.1.100"
            # Missing other keys
        }

        result = sample_node.compare_with(incomplete_data)

        assert result["status"] == "CONDITIONAL"
        assert len(result["extra_keys"]) > 0
        assert "gpu_type" in result["extra_keys"]

    def test_compare_with_value_mismatches(self, sample_node, sample_node_data):
        """Test comparison with different values returns FAIL"""
        modified_data = sample_node_data.copy()
        modified_data["gpu_type"] = "Nvidia RTX 3090"  # Different value
        modified_data["ip"] = "192.168.1.200"  # Different value

        result = sample_node.compare_with(modified_data)

        assert result["status"] == "FAIL"
        assert len(result["value_mismatches"]) == 2

        # Check that mismatches are properly recorded
        mismatches = {mismatch[0]: (mismatch[1], mismatch[2]) for mismatch in result["value_mismatches"]}
        assert "gpu_type" in mismatches
        assert mismatches["gpu_type"] == ("Nvidia H200", "Nvidia RTX 3090")
        assert "ip" in mismatches
        assert mismatches["ip"] == ("10.0.0.10", "192.168.1.200")

    def test_string_representation(self, sample_node):
        """Test string representation of Node"""
        node_str = str(sample_node)
        assert "test-node-1" in node_str
        assert "Nvidia H200" in node_str

    def test_repr_representation(self, sample_node):
        """Test repr representation of Node"""
        node_repr = repr(sample_node)
        assert "test-node-1" in node_repr
        assert "Nvidia H200" in node_repr

    @pytest.mark.parametrize("missing_field,expected_default", [
        ("ip", ""),
        ("gpu_type", ""),
        ("secure_boot", False),
        ("monitoring_enabled", False),
        ("tags", []),
    ])
    def test_default_values(self, missing_field, expected_default):
        """Test that missing fields get appropriate default values"""
        data = {"hostname": "test-node"}
        data.pop(missing_field, None)  # Remove the field to test default

        node = Node(data)
        actual_value = getattr(node, missing_field)
        assert actual_value == expected_default

    def test_hostname_default_value(self):
        """Test hostname default value separately"""
        data = {}  # No hostname provided
        node = Node(data)
        assert node.hostname == ""
