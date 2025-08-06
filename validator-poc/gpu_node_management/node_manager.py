"""
Node manager for GPU node operations.
"""
import yaml
import logging
from typing import List

from .node import Node
from .etcd_client import EtcdClient


class NodeManager:
    """Manages GPU nodes and their operations"""

    def __init__(self, etcd_url: str, logger: logging.Logger):
        self.etcd_client = EtcdClient(etcd_url)
        self.logger = logger

    def load_nodes_from_file(self, file_path: str) -> List[Node]:
        """Load nodes from YAML file"""
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            nodes = [Node(node_data) for node_data in data.get("nodes", [])]
            self.logger.info(f"Loaded {len(nodes)} nodes from {file_path}")
            return nodes
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.error(f"Error loading file {file_path}: {e}")
            return []

    def put_nodes(self, file_path: str) -> None:
        """Update nodes in etcd from YAML file"""
        self.logger.info(f"Starting to update nodes from {file_path}")
        nodes = self.load_nodes_from_file(file_path)
        if not nodes:
            self.logger.warning("No nodes loaded, aborting update operation")
            return

        success_count = 0
        for node in nodes:
            self.logger.info(f"Updating {node.hostname}...")

            if self.etcd_client.put_node(node):
                self.logger.info(f"Successfully stored {node.hostname} to etcd")
                success_count += 1
            else:
                self.logger.error(f"Failed to store {node.hostname} to etcd")

        self.logger.info(f"Update operation completed: {success_count}/{len(nodes)} nodes updated successfully")

    def get_node_info(self, hostname: str) -> None:
        """Get node information from etcd"""
        self.logger.info(f"Retrieving info for {hostname}...")

        stored_data = self.etcd_client.get_node(hostname)
        if stored_data is None:
            self.logger.error(f"Node {hostname} not found in etcd")
            return

        self.logger.info(f"Node {hostname} found:")
        # Print to console for user visibility, but also log
        node_yaml = yaml.dump(stored_data, default_flow_style=False)
        print(node_yaml)
        self.logger.debug(f"Node {hostname} data: {node_yaml}")

    def validate_nodes(self, file_path: str) -> None:
        """Validate nodes from YAML file against etcd data"""
        self.logger.info(f"Starting validation of nodes from {file_path}")
        nodes = self.load_nodes_from_file(file_path)
        if not nodes:
            self.logger.warning("No nodes loaded, aborting validation operation")
            return

        pass_count = 0
        conditional_count = 0
        fail_count = 0

        for node in nodes:
            self.logger.info(f"Validating {node.hostname}...")

            # Retrieve and compare (don't upload during validation)
            stored_data = self.etcd_client.get_node(node.hostname)
            if stored_data is None:
                self.logger.error(f"Node {node.hostname} not found in etcd")
                fail_count += 1
                continue

            result = node.compare_with(stored_data)

            if result["status"] == "PASS":
                self.logger.info(f"PASS: {node.hostname} - All values match")
                pass_count += 1
            elif result["status"] == "CONDITIONAL":
                self.logger.warning(f"CONDITIONAL: {node.hostname} - Missing keys in etcd: {result['extra_keys']}")
                conditional_count += 1
            elif result["status"] == "FAIL":
                self.logger.error(f"FAIL: {node.hostname} - Value mismatches:")
                for k, expected, actual in result["value_mismatches"]:
                    self.logger.error(f"    - {k}: expected={expected}, actual={actual}")
                fail_count += 1

        self.logger.info(f"Validation completed: {pass_count} passed, {conditional_count} conditional, {fail_count} failed")
