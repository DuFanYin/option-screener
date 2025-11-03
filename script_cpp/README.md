# Option Screener - C++ Version

C++ implementation of the option screener, matching the structure of `script_minimal`.

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
# Build and run automatically
./build_and_run.sh
```

### Manual Build Instructions

```bash
# Create build directory
mkdir build
cd build

# Configure
cmake ..

# Build
cmake --build .

# Run example
./bin/option_screener
```

### Build Options

- **Release mode** (default): `cmake -DCMAKE_BUILD_TYPE=Release ..`
- **Debug mode**: `cmake -DCMAKE_BUILD_TYPE=Debug ..`

## Usage

```cpp
#include "loader.hpp"
#include "factory/factory.hpp"

auto [options, spot] = load_option_snapshot("data/pltr.json");
StrategyFactory factory(options, spot.value());

StrategyFilter s_filter;
s_filter.straddles = true;

ConfigFilter c_filter;
c_filter.min_oi = 5;
c_filter.min_price = 0.05;
c_filter.days_to_expiry_range = std::make_tuple(0, 30);
c_filter.direction = Direction::SHORT;
c_filter.credit_range = std::make_tuple(0.0, 2500.0);

auto results = factory.strategy(s_filter, c_filter)
    .rank("cost")
    .top(10);
```

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

