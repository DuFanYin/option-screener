#!/bin/bash

# Build or run option_screener
# Usage: ./build_and_run.sh [build|run]
#   build - Only build (default)
#   run   - Only run (must be built first)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="${SCRIPT_DIR}/build"
MODE="${1:-build}"
DATA_FILE="pltr.json"

if [ "${MODE}" = "build" ]; then
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    cmake .. && cmake --build .
elif [ "${MODE}" = "run" ]; then
    if [ ! -f "${BUILD_DIR}/bin/option_screener" ]; then
        echo "Error: Executable not found. Run './build_and_run.sh build' first."
        exit 1
    fi
    
    # Check config.json exists
    CONFIG_FILE="${SCRIPT_DIR}/config.json"
    if [ ! -f "${CONFIG_FILE}" ]; then
        echo "Error: config.json not found: ${CONFIG_FILE}"
        exit 1
    fi
    
    # Check data file exists (data folder is at same level as script_cpp)
    DATA_PATH="${SCRIPT_DIR}/../data/${DATA_FILE}"
    if [ ! -f "${DATA_PATH}" ]; then
        echo "Error: Data file not found: ${DATA_PATH}"
        exit 1
    fi
    
    cd "${SCRIPT_DIR}"
    "${BUILD_DIR}/bin/option_screener" config.json "${DATA_PATH}"
else
    echo "Usage: $0 [build|run]"
    exit 1
fi

