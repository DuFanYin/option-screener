cmake_minimum_required(VERSION 3.15)
project(option_screener VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# Include directories - headers are in include/
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Download nlohmann/json single header if not present
set(JSON_HEADER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/nlohmann)
set(JSON_HEADER_FILE ${JSON_HEADER_DIR}/json.hpp)

if(NOT EXISTS ${JSON_HEADER_FILE})
    message(STATUS "Downloading nlohmann/json single header...")
    file(MAKE_DIRECTORY ${JSON_HEADER_DIR})
    file(DOWNLOAD 
        https://github.com/nlohmann/json/releases/download/v3.11.3/json.hpp
        ${JSON_HEADER_FILE}
        SHOW_PROGRESS
        TLS_VERIFY ON
    )
endif()

# Add nlohmann/json include directory
include_directories(${JSON_HEADER_DIR})

# Source files (only .cpp files)
set(SOURCES
    src/object.cpp
    src/loader.cpp
    src/config.cpp
    src/factory/factory.cpp
    src/factory/option_filter.cpp
    src/strategy/strategy_class.cpp
    src/strategy/generator_class.cpp
)

# Create library
add_library(option_screener_lib STATIC ${SOURCES})
target_include_directories(option_screener_lib PUBLIC 
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${JSON_HEADER_DIR}
)

# Create executable
add_executable(option_screener example.cpp)
target_link_libraries(option_screener PRIVATE option_screener_lib)

# Installation (optional)
install(TARGETS option_screener DESTINATION bin)
install(TARGETS option_screener_lib DESTINATION lib)
install(DIRECTORY include/ DESTINATION include FILES_MATCHING PATTERN "*.hpp")
