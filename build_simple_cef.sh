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
    
    # Copy module to tests directory for easy testing
    cp simple_cef*.so ../tests/
    echo "Module copied to tests/ directory"
    
    echo ""
    echo "To test, run:"
    echo "  cd tests"  
    echo "  source ../.venv/bin/activate"
    echo "  DYLD_FRAMEWORK_PATH=. python test_simple_import.py"
    echo ""
    echo "Module successfully built!"
    echo "- SimpleCefBrowser(width, height) - creates headless browser"
    echo "- get_pixel_buffer() - returns raw BGRA pixel array"
    echo "- Direct memory access for video streaming"
else
    echo "Build failed!"
    exit 1
fi