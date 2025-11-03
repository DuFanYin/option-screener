# Option Screener - C++ Version

C++ implementation of the option screener

## Project Structure

Standard C++ project layout with separate header and source files:

```
script_cpp/
├── CMakeLists.txt          # Root CMake configuration
├── example.cpp             # Example usage program
├── README.md               # This file
├── include/                # Header files (.hpp)
│   ├── object.hpp          # Option, Direction, StrategyFilter, ConfigFilter
│   ├── loader.hpp          # JSON loading functionality
│   ├── factory/
│   │   ├── factory.hpp     # StrategyFactory, StrategyList
│   │   └── option_filter.hpp  # OptionFilter
│   └── strategy/
│       ├── strategy_class.hpp   # Strategy base class, Straddle
│       └── generator_class.hpp  # Strategy generators
└── src/                    # Source files (.cpp)
    ├── object.cpp
    ├── loader.cpp
    ├── factory/
    │   ├── factory.cpp
    │   └── option_filter.cpp
    └── strategy/
        ├── strategy_class.cpp
        └── generator_class.cpp
```

## Building

### Prerequisites

- CMake 3.15 or higher
- C++17 compatible compiler (GCC 7+, Clang 5+, MSVC 2017+)
- nlohmann/json (automatically fetched if not found)

### Quick Start (Recommended)

```bash
# Build only
./build_and_run.sh build
# or simply
./build_and_run.sh

# Run only (must be built first)
./build_and_run.sh run
```

### Build Options

To build in a specific mode, modify the build script or run CMake manually:
- **Release mode** (default): `cmake -DCMAKE_BUILD_TYPE=Release ..`
- **Debug mode**: `cmake -DCMAKE_BUILD_TYPE=Debug ..`

## Usage

The C++ version uses a JSON configuration file to avoid recompiling when changing parameters.

### Configuration File (config.json)

Create a `config.json` file in the `script_cpp` directory with your settings:

```json
{
  "strategy_filter": {
    "single_calls": true,
    "iron_condors": false,
    "straddles": true,
    "strangles": false
  },
  
  "config_filter": {
    "min_volume": null,
    "min_oi": 5,
    "min_price": 0.05,
    "expiry": null,
    "days_to_expiry_range": [0, 30],
    "volume_ratio_range": null,
    "max_bid_ask_spread": null,
    "direction": "SHORT",
    "debit_range": null,
    "credit_range": [0, 2500],
    "potential_gain_range": null,
    "potential_loss_range": null,
    "rr_range": null,
    "net_delta_range": null,
    "net_theta_range": null,
    "net_vega_range": null,
    "iv_range": null
  },
  
  "ranking": {
    "key": "cost",
    "top_n": 10
  }
}
```

### Running

Always use the build script:

```bash
./build_and_run.sh run
```

The script automatically checks for `config.json` and the data file before running.

## Design Notes

- **Standard C++ project structure**: Headers in `include/`, sources in `src/`
- **C++17 features**: std::optional, structured bindings, etc.
- **Smart pointers**: std::unique_ptr for memory management
- **CMake build system**: Handles dependencies (nlohmann/json via FetchContent)
- **Matches Python structure**: Folder structure mirrors `script_minimal` for easy comparison

## Dependencies

- **nlohmann/json**: JSON parsing (automatically fetched via FetchContent)

## Project Organization

This follows standard C++ project conventions:
- **include/**: Public header files (.hpp)
- **src/**: Implementation files (.cpp)
- **build/**: CMake build directory (generated)
- Headers and sources maintain the same directory structure for easy navigation

