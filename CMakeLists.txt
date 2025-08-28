cmake_minimum_required(VERSION 3.20)
project(ScreenCapture)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Detect OS for platform-specific settings
if(APPLE)
    set(OS_MACOSX 1)
endif()

# Find packages
find_package(PkgConfig REQUIRED)

# CEF configuration
set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/third_party/cef")
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CEF_ROOT}/cmake")

# Add CEF binary and resource paths
if(OS_MACOSX)
  set(CEF_TARGET "Chromium Embedded Framework")
  set(CEF_BINARY_DIR "${CEF_ROOT}/Release")
  set(CEF_RESOURCE_DIR "${CEF_ROOT}/Resources")
endif()

# Include CEF headers
include_directories(${CEF_ROOT})

# Link CEF libraries
if(OS_MACOSX)
  set(CEF_LIBRARIES
    "${CEF_BINARY_DIR}/Chromium Embedded Framework.framework/Chromium Embedded Framework"
    "${CEF_ROOT}/build/libcef_dll_wrapper/libcef_dll_wrapper.a"
  )
endif()

# Real codec libraries
find_package(PkgConfig REQUIRED)
pkg_check_modules(VPX REQUIRED vpx)
pkg_check_modules(X264 REQUIRED x264)
pkg_check_modules(FFMPEG REQUIRED libavcodec libavformat libavutil libswscale)

# Check if optional files exist and build accordingly
set(SCREEN_CAPTURE_SOURCES
    src/main.cpp
    src/screen_capture_handler.cpp
    src/tiled_encoder.cpp
)

# Add optional source files if they exist
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/motion_detector.cpp")
    list(APPEND SCREEN_CAPTURE_SOURCES src/motion_detector.cpp)
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/websocket_server.cpp")
    list(APPEND SCREEN_CAPTURE_SOURCES src/websocket_server.cpp)
endif()

# Main executable
add_executable(screen_capture ${SCREEN_CAPTURE_SOURCES})

target_include_directories(screen_capture PRIVATE
    ${CEF_ROOT}
    ${VPX_INCLUDE_DIRS}
    ${X264_INCLUDE_DIRS}
    ${FFMPEG_INCLUDE_DIRS}
    include/
)

target_link_libraries(screen_capture
    ${CEF_LIBRARIES}
    ${VPX_LIBRARIES}
    ${X264_LIBRARIES}
    ${FFMPEG_LIBRARIES}
    websockets
    pthread
)

# WASM decoder module
if(EMSCRIPTEN)
    add_executable(wasm_decoder
        src/wasm_decoder.cpp
        src/tile_decoder.cpp
    )
    
    set_target_properties(wasm_decoder PROPERTIES
        LINK_FLAGS "-s WASM=1 -s EXPORTED_FUNCTIONS=['_decode_tile','_init_decoder'] -s EXPORTED_RUNTIME_METHODS=['ccall','cwrap'] -s ALLOW_MEMORY_GROWTH=1"
    )
    
    target_link_libraries(wasm_decoder
        ${VPX_LIBRARIES}
        ${X264_LIBRARIES}
        ${FFMPEG_LIBRARIES}
    )
endif()

# Simple CEF Python module with pybind11
find_package(pybind11 QUIET)
if(NOT pybind11_FOUND)
    # Try to find pybind11 via the virtual environment Python
    execute_process(
        COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/.venv/bin/python -c "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(pybind11_DIR)
        find_package(pybind11 QUIET PATHS ${pybind11_DIR})
    endif()
endif()

if(pybind11_FOUND)
    pybind11_add_module(simple_cef
        src/simple_cef_browser.cpp
        src/python_bindings.cpp
    )
    
    target_include_directories(simple_cef PRIVATE
        ${CEF_ROOT}
        include/
    )
    
    target_link_libraries(simple_cef PRIVATE
        ${CEF_LIBRARIES}
    )
    
    # Set proper RPATH for macOS
    if(OS_MACOSX)
        set_target_properties(simple_cef PROPERTIES
            INSTALL_RPATH "@loader_path;@loader_path/../third_party/cef/Release"
            BUILD_WITH_INSTALL_RPATH TRUE
        )
    endif()
else()
    message(WARNING "pybind11 not found. Python module will not be built.")
endif()

# Copy resources
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/web/index.html 
               ${CMAKE_CURRENT_BINARY_DIR}/web/index.html COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/web/main.js 
               ${CMAKE_CURRENT_BINARY_DIR}/web/main.js COPYONLY)