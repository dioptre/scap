#!/bin/bash

# Build script for Screen Capture Tiling System

set -e

echo "Building Screen Capture Tiling System..."

# Setup CEF if not exists
if [ ! -d "third_party/cef" ]; then
    echo "CEF not found. Choose installation method:"
    echo "1. Download prebuilt binaries (5 minutes, ~200MB)"
    echo "2. Build from source (4+ hours, ~40GB)"
    echo ""
    read -p "Enter choice [1-2] (default: 1): " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            echo "Using prebuilt CEF binaries..."
            chmod +x download_cef_direct.sh
            ./download_cef_direct.sh
            ;;
        2)
            echo "Building CEF from source..."
            chmod +x build_cef_from_source.sh
            ./build_cef_from_source.sh
            ;;
        *)
            echo "Invalid choice. Using prebuilt binaries (default)..."
            chmod +x download_cef_direct.sh
            ./download_cef_direct.sh
            ;;
    esac
fi

# Create build directory
mkdir -p build
cd build

# Configure with CMake for native build
echo "Configuring native build..."
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build native executable
echo "Building native executable..."
make -j$(nproc)

# Build WASM module
echo "Building WASM module..."
cd ..
mkdir -p build-wasm
cd build-wasm

# Configure with Emscripten
emcmake cmake .. -DCMAKE_BUILD_TYPE=Release
emmake make -j$(nproc)

# Copy WASM files to web directory
cp wasm_decoder.js ../web/
cp wasm_decoder.wasm ../web/

cd ..

echo "Build completed successfully!"
echo ""
echo "To run the system:"
echo "1. Install Python dependencies: pip install -r requirements.txt"
echo "2. Start the Ray FastAPI server: python src/websocket_server.py" 
echo "3. Start the C++ screen capture: ./build/screen_capture"
echo "4. Open browser to: http://localhost:8000"