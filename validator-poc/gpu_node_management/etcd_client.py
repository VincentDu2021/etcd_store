"""
etcd client for GPU node management.
"""
import base64
import requests
import yaml
from typing import Dict, Optional, Any

from .node import Node


class EtcdClient:
    """Handles etcd operations with base64 encoding/decoding"""

    def __init__(self, etcd_url: str):
        self.etcd_url = etcd_url

    @staticmethod
    def _b64_encode(s: str) -> str:
        """Base64 encode string"""
        return base64.b64encode(s.encode()).decode()

    @staticmethod
    def _b64_decode(s: str) -> str:
        """Base64 decode string"""
        return base64.b64decode(s).decode()

    def put_node(self, node: Node) -> bool:
        """Store a node in etcd"""
        key = f"/gpu/nodes/{node.hostname}"
        value = node.to_yaml()
        payload = {"key": self._b64_encode(key), "value": self._b64_encode(value)}

        try:
            response = requests.post(f"{self.etcd_url}/v3/kv/put", json=payload)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_node(self, hostname: str) -> Optional[Dict[str, Any]]:
        """Retrieve a node from etcd"""
        key = f"/gpu/nodes/{hostname}"
        payload = {"key": self._b64_encode(key)}

        try:
            response = requests.post(f"{self.etcd_url}/v3/kv/range", json=payload)
            if response.status_code != 200:
                return None

            data = response.json()
            if "kvs" not in data or not data["kvs"]:
                return None

            return yaml.safe_load(self._b64_decode(data["kvs"][0]["value"]))
        except (requests.RequestException, yaml.YAMLError):
            return None
