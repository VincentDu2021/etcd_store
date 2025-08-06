#!/bin/bash

# GPU Node Management Tool - etcd Setup Script
# This script helps set up a local etcd instance for testing

set -e

ETCD_VERSION="v3.5.9"
ETCD_PORT="2379"
ETCD_PEER_PORT="2380"
DOCKER_CMD="docker"  # Will be set to "sudo docker" if needed

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if command -v docker &> /dev/null; then
        # Try without sudo first
        if docker info &> /dev/null; then
            DOCKER_CMD="docker"
            return 0
        # Try with sudo
        elif sudo docker info &> /dev/null 2>&1; then
            DOCKER_CMD="sudo docker"
            print_warning "Using sudo for Docker commands (user not in docker group)"
            return 0
        else
            print_error "Docker is installed but not running"
            return 1
        fi
    else
        return 1
    fi
}

start_etcd_docker() {
    print_status "Starting etcd using Docker..."

    # Stop existing container if running
    if $DOCKER_CMD ps | grep -q etcd-server; then
        print_warning "Stopping existing etcd-server container..."
        $DOCKER_CMD stop etcd-server
    fi

    # Remove container if exists
    if $DOCKER_CMD ps -a | grep -q etcd-server; then
        $DOCKER_CMD rm etcd-server
    fi

    # Start new etcd container
    $DOCKER_CMD run -d \
        --name etcd-server \
        -p ${ETCD_PORT}:2379 \
        -p ${ETCD_PEER_PORT}:2380 \
        quay.io/coreos/etcd:${ETCD_VERSION} \
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

    # Wait for etcd to start
    print_status "Waiting for etcd to start..."
    sleep 5

    # Test connection
    test_etcd_connection
}

test_etcd_connection() {
    print_status "Testing etcd connection..."

    if command -v curl &> /dev/null; then
        if curl -s http://localhost:${ETCD_PORT}/version > /dev/null; then
            print_status "✅ etcd is running and accessible"
            echo
            echo "etcd is now available at:"
            echo "  Client URL: http://localhost:${ETCD_PORT}"
            echo "  Peer URL: http://localhost:${ETCD_PEER_PORT}"
            echo
            echo "You can now run tests with:"
            echo "  pytest tests/"
            echo
            echo "Or use the application with:"
            echo "  python node_validator.py --etcd http://localhost:${ETCD_PORT} put --file tests/data/gpu_nodes.yaml"
            return 0
        else
            print_error "❌ etcd is not responding"
            return 1
        fi
    else
        print_warning "curl not available, cannot test connection"
        print_status "Assuming etcd is running..."
        return 0
    fi
}

stop_etcd_docker() {
    print_status "Stopping etcd Docker container..."

    if $DOCKER_CMD ps | grep -q etcd-server; then
        $DOCKER_CMD stop etcd-server
        print_status "✅ etcd container stopped"
    else
        print_warning "etcd-server container is not running"
    fi

    if $DOCKER_CMD ps -a | grep -q etcd-server; then
        $DOCKER_CMD rm etcd-server
        print_status "✅ etcd container removed"
    fi
}

show_status() {
    print_status "Checking etcd status..."

    if check_docker; then
        if $DOCKER_CMD ps | grep -q etcd-server; then
            print_status "✅ etcd Docker container is running"
            test_etcd_connection
        else
            print_warning "❌ etcd Docker container is not running"
        fi
    else
        print_warning "Docker not available"
    fi

    # Check if etcd is accessible regardless of how it's running
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:${ETCD_PORT}/version > /dev/null; then
            print_status "✅ etcd is accessible at http://localhost:${ETCD_PORT}"
        else
            print_warning "❌ etcd is not accessible at http://localhost:${ETCD_PORT}"
        fi
    fi
}

show_help() {
    echo "GPU Node Management Tool - etcd Setup Script"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start etcd using Docker"
    echo "  stop      Stop and remove etcd Docker container"
    echo "  status    Check etcd status"
    echo "  test      Test etcd connection"
    echo "  clean     Clear all GPU node data from etcd"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start     # Start etcd for testing"
    echo "  $0 status    # Check if etcd is running"
    echo "  $0 clean     # Clear all test data"
    echo "  $0 stop      # Stop etcd when done"
    echo
    echo "Prerequisites:"
    echo "  - Docker installed and running"
    echo "  - Ports 2379 and 2380 available"
    echo "  - May require sudo if user not in docker group"
    echo
    echo "After starting etcd, you can run:"
    echo "  pytest tests/                    # Run all tests"
    echo "  python node_validator.py --help  # Use the application"
}

clean_etcd_data() {
    print_status "Cleaning GPU node data from etcd..."

    if command -v curl &> /dev/null; then
        # First, let's see if etcd is accessible
        if ! curl -s http://localhost:${ETCD_PORT}/version > /dev/null; then
            print_error "etcd is not accessible at http://localhost:${ETCD_PORT}"
            return 1
        fi

        # Delete all keys with the /gpu/nodes/ prefix using etcd v3 API
        # /gpu/nodes/ base64 encoded = L2dwdS9ub2Rlcy8=
        # /gpu/nodes0 base64 encoded = L2dwdS9ub2RlczA= (range_end for prefix deletion)
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d '{"key":"L2dwdS9ub2Rlcy8=","range_end":"L2dwdS9ub2RlczA="}' \
            http://localhost:${ETCD_PORT}/v3/kv/deleterange)

        if echo "$response" | grep -q '"deleted"'; then
            deleted_count=$(echo "$response" | grep -o '"deleted":"[0-9]*"' | cut -d'"' -f4)
            if [ "$deleted_count" -gt 0 ] 2>/dev/null; then
                print_status "✅ Cleaned up $deleted_count etcd keys"
            else
                print_status "✅ No GPU node data found to clean"
            fi
        else
            print_status "✅ Cleanup completed (no keys found)"
        fi
    else
        print_error "curl not available, cannot clean etcd data"
        return 1
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        if check_docker; then
            start_etcd_docker
        else
            print_error "Docker is required but not available"
            print_error "Please install Docker and try again"
            exit 1
        fi
        ;;
    stop)
        if check_docker; then
            stop_etcd_docker
        else
            print_error "Docker not available"
            exit 1
        fi
        ;;
    status)
        show_status
        ;;
    test)
        test_etcd_connection
        ;;
    clean)
        clean_etcd_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
