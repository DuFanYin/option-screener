#!/bin/bash

# Timing script to compare Python vs C++ execution times
# Usage: ./timing.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="${SCRIPT_DIR}/config.json"
DATA_FILE="${SCRIPT_DIR}/data/pltr.json"
CPP_EXEC="${SCRIPT_DIR}/cpp/build/bin/option_screener"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if config and data files exist
if [ ! -f "${CONFIG_FILE}" ]; then
    echo -e "${RED}Error: config.json not found: ${CONFIG_FILE}${NC}"
    exit 1
fi

if [ ! -f "${DATA_FILE}" ]; then
    echo -e "${RED}Error: Data file not found: ${DATA_FILE}${NC}"
    exit 1
fi

# Check if C++ executable exists
if [ ! -f "${CPP_EXEC}" ]; then
    echo -e "${YELLOW}Warning: C++ executable not found. Building...${NC}"
    cd "${SCRIPT_DIR}"
    ./build_and_run.sh build
fi

# Time Python execution - time writes to stderr, script output to stdout
(/usr/bin/time -p python3 "${SCRIPT_DIR}/run_script.py" > /tmp/python_output.txt) 2> /tmp/python_time.txt
PYTHON_TIME=$(grep -E "^real " /tmp/python_time.txt | awk '{print $2}' || echo "0")
PYTHON_COUNT=$(grep -oE 'Found [0-9]+' /tmp/python_output.txt | awk '{print $2}' | head -1 || echo "0")

# Time C++ execution - time writes to stderr, executable output to stdout
(/usr/bin/time -p "${CPP_EXEC}" "${CONFIG_FILE}" "${DATA_FILE}" > /tmp/cpp_output.txt) 2> /tmp/cpp_time.txt
CPP_TIME=$(grep -E "^real " /tmp/cpp_time.txt | awk '{print $2}' || echo "0")
CPP_COUNT=$(grep -oE 'Found [0-9]+' /tmp/cpp_output.txt | awk '{print $2}' | head -1 || echo "0")

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Timing Results${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Python:${NC}"
echo -e "  Strategies found: ${PYTHON_COUNT}"
echo -e "  Execution time: ${PYTHON_TIME} seconds"
echo ""
echo -e "${GREEN}C++:${NC}"
echo -e "  Strategies found: ${CPP_COUNT}"
echo -e "  Execution time: ${CPP_TIME} seconds"
echo ""

# Calculate speedup using awk (more portable than bc)
if [ -n "$PYTHON_TIME" ] && [ -n "$CPP_TIME" ] && [ "$CPP_TIME" != "0" ]; then
    SPEEDUP=$(awk "BEGIN {printf \"%.2f\", $PYTHON_TIME / $CPP_TIME}")
    echo -e "${YELLOW}Speedup: ${SPEEDUP}x${NC}"
    
    # Use awk comparison with explicit if-else instead of ternary
    SPEEDUP_RESULT=$(awk -v py="$PYTHON_TIME" -v cpp="$CPP_TIME" "BEGIN {if ((py / cpp) > 1) print 1; else print 0}")
    if [ "$SPEEDUP_RESULT" = "1" ]; then
        echo -e "${GREEN}C++ is ${SPEEDUP}x faster than Python${NC}"
    else
        INV_SPEEDUP=$(awk "BEGIN {printf \"%.2f\", $CPP_TIME / $PYTHON_TIME}")
        echo -e "${YELLOW}Python is ${INV_SPEEDUP}x faster than C++${NC}"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"

# Cleanup
rm -f /tmp/python_output.txt /tmp/cpp_output.txt /tmp/python_time.txt /tmp/cpp_time.txt

