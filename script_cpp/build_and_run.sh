#!/bin/bash

# Build and run script for option_screener
# This script will build the project and run the example

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="${SCRIPT_DIR}/build"

echo -e "${GREEN}Building option_screener...${NC}"

# Create build directory if it doesn't exist
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Configure CMake
echo -e "${YELLOW}Configuring CMake...${NC}"
cmake .. || {
    echo -e "${RED}CMake configuration failed!${NC}"
    exit 1
}

# Build project
echo -e "${YELLOW}Building project...${NC}"
cmake --build . || {
    echo -e "${RED}Build failed!${NC}"
    exit 1
}

echo -e "${GREEN}Build successful!${NC}"

# Run the example
echo -e "${GREEN}Running example...${NC}"
echo "----------------------------------------"
./bin/option_screener || {
    echo -e "${RED}Execution failed!${NC}"
    exit 1
}
echo "----------------------------------------"
echo -e "${GREEN}Done!${NC}"

