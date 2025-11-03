#!/bin/bash

# Build or run option_screener
# Usage: ./build_and_run.sh [build|run]
#   build - Only build (default)
#   run   - Only run (must be built first)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CPP_DIR="${SCRIPT_DIR}/cpp"
BUILD_DIR="${CPP_DIR}/build"
MODE="${1:-build}"
DATA_FILE="pltr.json"

if [ "${MODE}" = "build" ]; then
    # Remove old CMakeCache.txt if it exists from previous location
    if [ -f "${BUILD_DIR}/CMakeCache.txt" ]; then
        rm -f "${BUILD_DIR}/CMakeCache.txt"
    fi
    mkdir -p "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    cmake "${CPP_DIR}" && cmake --build .
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
    
    # Check data file exists (data folder is at root level)
    DATA_PATH="${SCRIPT_DIR}/data/${DATA_FILE}"
    if [ ! -f "${DATA_PATH}" ]; then
        echo "Error: Data file not found: ${DATA_PATH}"
        exit 1
    fi
    
    cd "${SCRIPT_DIR}"
    "${BUILD_DIR}/bin/option_screener" "${CONFIG_FILE}" "${DATA_PATH}"
else
    echo "Usage: $0 [build|run]"
    exit 1
fi

