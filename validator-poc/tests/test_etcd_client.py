"""
Unit tests for the EtcdClient class.
"""
import pytest
import base64
import json
from unittest.mock import Mock, patch, MagicMock
import requests
import yaml

from gpu_node_management import EtcdClient, Node


class TestEtcdClient:
    """Test cases for EtcdClient class"""

    def test_initialization(self):
        """Test EtcdClient initialization"""
        etcd_url = "http://test-etcd:2380"
        client = EtcdClient(etcd_url)
        assert client.etcd_url == etcd_url

    def test_b64_encode(self):
        """Test base64 encoding"""
        test_string = "hello world"
        expected = base64.b64encode(test_string.encode()).decode()
        result = EtcdClient._b64_encode(test_string)
        assert result == expected

    def test_b64_decode(self):
        """Test base64 decoding"""
        test_string = "hello world"
        encoded = base64.b64encode(test_string.encode()).decode()
        result = EtcdClient._b64_decode(encoded)
        assert result == test_string

    @patch('requests.post')
    def test_put_node_success(self, mock_post, sample_node):
        """Test successful node storage in etcd"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.put_node(sample_node)

        assert result is True
        mock_post.assert_called_once()

        # Verify the call was made with correct parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test-etcd:2380/v3/kv/put"

        # Verify payload structure
        payload = call_args[1]['json']
        assert 'key' in payload
        assert 'value' in payload

        # Verify key is correctly encoded
        decoded_key = base64.b64decode(payload['key']).decode()
        assert decoded_key == f"/gpu/nodes/{sample_node.hostname}"

    @patch('requests.post')
    def test_put_node_failure_status_code(self, mock_post, sample_node):
        """Test node storage failure due to bad status code"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.put_node(sample_node)

        assert result is False

    @patch('requests.post')
    def test_put_node_failure_exception(self, mock_post, sample_node):
        """Test node storage failure due to request exception"""
        mock_post.side_effect = requests.RequestException("Connection failed")

        client = EtcdClient("http://test-etcd:2380")
        result = client.put_node(sample_node)

        assert result is False

    @patch('requests.post')
    def test_get_node_success(self, mock_post, sample_node_data):
        """Test successful node retrieval from etcd"""
        # Prepare mock response
        yaml_data = yaml.dump(sample_node_data)
        encoded_value = base64.b64encode(yaml_data.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "kvs": [{"value": encoded_value}]
        }
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("test-gpu-01")

        assert result == sample_node_data
        mock_post.assert_called_once()

        # Verify the call was made with correct parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://test-etcd:2380/v3/kv/range"

        payload = call_args[1]['json']
        decoded_key = base64.b64decode(payload['key']).decode()
        assert decoded_key == "/gpu/nodes/test-gpu-01"

    @patch('requests.post')
    def test_get_node_not_found_status_code(self, mock_post):
        """Test node retrieval failure due to bad status code"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("nonexistent-node")

        assert result is None

    @patch('requests.post')
    def test_get_node_not_found_empty_response(self, mock_post):
        """Test node retrieval when etcd returns empty response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"kvs": []}
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("nonexistent-node")

        assert result is None

    @patch('requests.post')
    def test_get_node_not_found_no_kvs(self, mock_post):
        """Test node retrieval when etcd response has no kvs field"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("nonexistent-node")

        assert result is None

    @patch('requests.post')
    def test_get_node_failure_exception(self, mock_post):
        """Test node retrieval failure due to request exception"""
        mock_post.side_effect = requests.RequestException("Connection failed")

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("test-node")

        assert result is None

    @patch('requests.post')
    def test_get_node_failure_yaml_error(self, mock_post):
        """Test node retrieval failure due to YAML parsing error"""
        # Prepare mock response with invalid YAML
        invalid_yaml = "invalid: yaml: content: ["
        encoded_value = base64.b64encode(invalid_yaml.encode()).decode()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "kvs": [{"value": encoded_value}]
        }
        mock_post.return_value = mock_response

        client = EtcdClient("http://test-etcd:2380")
        result = client.get_node("test-node")

        assert result is None
