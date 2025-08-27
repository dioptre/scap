cmake_minimum_required(VERSION 3.20)
project(ScreenCapture)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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
    "${CEF_ROOT}/build/libcef_dll_wrapper/Release/libcef_dll_wrapper.a"
  )
endif()

# Real codec libraries
find_package(PkgConfig REQUIRED)
pkg_check_modules(VPX REQUIRED vpx)
pkg_check_modules(X264 REQUIRED x264)
pkg_check_modules(FFMPEG REQUIRED libavcodec libavformat libavutil libswscale)

# Main executable
add_executable(screen_capture
    src/main.cpp
    src/screen_capture_handler.cpp
    src/tiled_encoder.cpp
    src/motion_detector.cpp
    src/websocket_server.cpp
)

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

# Copy resources
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/web/index.html 
               ${CMAKE_CURRENT_BINARY_DIR}/web/index.html COPYONLY)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/web/main.js 
               ${CMAKE_CURRENT_BINARY_DIR}/web/main.js COPYONLY)