"""
Node class for representing GPU nodes.
"""
import yaml
from typing import Dict, List, Any


class Node:
    """Represents a GPU node with its specifications"""

    def __init__(self, data: Dict[str, Any]):
        self.hostname = data.get('hostname', '')
        self.ip = data.get('ip', '')
        self.gpu_type = data.get('gpu_type', '')
        self.bios_version = data.get('bios_version', '')
        self.nvidia_driver = data.get('nvidia_driver', '')
        self.cuda_version = data.get('cuda_version', '')
        self.os = data.get('os', '')
        self.kernel = data.get('kernel', '')
        self.secure_boot = data.get('secure_boot', False)
        self.monitoring_enabled = data.get('monitoring_enabled', False)
        self.tags = data.get('tags', [])
        self._raw_data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return self._raw_data

    def to_yaml(self) -> str:
        """Convert node to YAML string"""
        return yaml.dump(self._raw_data)

    def compare_with(self, other_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare this node with another node's data"""
        result = {"status": "PASS", "extra_keys": [], "value_mismatches": []}

        for k, v in self._raw_data.items():
            if k not in other_data:
                result["status"] = "CONDITIONAL"
                result["extra_keys"].append(k)
            elif other_data[k] != v:
                result["status"] = "FAIL"
                result["value_mismatches"].append((k, v, other_data[k]))

        return result

    def __str__(self) -> str:
        return f"Node({self.hostname}, {self.gpu_type})"

    def __repr__(self) -> str:
        return self.__str__()
