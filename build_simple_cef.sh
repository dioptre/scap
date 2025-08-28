#!/bin/bash

echo "Building Simple CEF Python Module"
echo "================================="

# Activate existing uv virtual environment
echo "Activating uv virtual environment..."
source .venv/bin/activate

# Install Python requirements
echo "Installing Python requirements..."
uv pip install -r requirements_simple.txt

# Build using CMake
echo "Building with CMake..."
mkdir -p build
cd build

cmake .. -DCMAKE_BUILD_TYPE=Release
make simple_cef

if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Python module: build/simple_cef*.so"
    
    # Fix library paths for macOS
    echo "Fixing library paths..."
    install_name_tool -change "@executable_path/../Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework" "@loader_path/Chromium Embedded Framework.framework/Chromium Embedded Framework" simple_cef*.so
    
    # Code sign for macOS security
    echo "Code signing..."
    codesign --force --sign - simple_cef*.so
    codesign --force --sign - ../third_party/cef/Release/Chromium\ Embedded\ Framework.framework/Chromium\ Embedded\ Framework
    
    # Copy module and framework
    cp simple_cef*.so ../
    cp simple_cef*.so ../src/
    cp simple_cef*.so ../tests/
    cp -r ../third_party/cef/Release/Chromium\ Embedded\ Framework.framework ../
    cp -r ../third_party/cef/Release/Chromium\ Embedded\ Framework.framework ../src/
    cp -r ../third_party/cef/Release/Chromium\ Embedded\ Framework.framework ../tests/
    
    echo "Module copied to all directories"
    
    # Generate protobuf files
    echo "Generating protobuf files..."
    protoc --python_out=src src/frame_data.proto
    
    echo ""
    echo "✅ Build complete!"
    echo "To run server:"
    echo "  source .venv/bin/activate"
    echo "  cd src && python websocket_server.py"
    echo ""
    echo "Or use: python start_server.py"
else
    echo "Build failed!"
    exit 1
fi