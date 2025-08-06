"""
GPU node management tool for etcd.
Main CLI interface and entry point.
"""
import argparse
import sys

from utils import setup_logging
from gpu_node_management import NodeManager


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="GPU node management tool for etcd.")
    parser.add_argument("--etcd", default="http://localhost:2380",
                        help="Base URL for etcd (default: http://localhost:2380)")
    parser.add_argument("--log-file", default="gpu_node_manager.log",
                        help="Log file path (default: gpu_node_manager.log)")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Log level (default: INFO)")

    subparsers = parser.add_subparsers(dest="action", help="Available actions")

    # Put command
    put_parser = subparsers.add_parser("put", help="Update nodes in etcd from YAML file")
    put_parser.add_argument("--file", required=True,
                           help="YAML file with GPU node specs to be updated to etcd")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get node information from etcd")
    get_parser.add_argument("--hostname", required=True,
                           help="Hostname of the node to retrieve")

    # Validate command
    validate_parser = subparsers.add_parser("validate",
                                          help="Validate existing node info with input")
    validate_parser.add_argument("--file", required=True,
                                help="YAML file with GPU node specs to be validated")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    logger = setup_logging(args.log_file, args.log_level)
    logger.info(f"Starting GPU node management tool - Action: {args.action}")

    # Create NodeManager instance
    node_manager = NodeManager(args.etcd, logger)

    try:
        # Execute the requested action
        if args.action == "put":
            node_manager.put_nodes(args.file)
        elif args.action == "get":
            node_manager.get_node_info(args.hostname)
        elif args.action == "validate":
            node_manager.validate_nodes(args.file)

        logger.info("Operation completed successfully")
    except Exception as e:
        logger.error(f"Operation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()