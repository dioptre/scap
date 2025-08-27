#!/bin/bash

# Direct CEF download with known working version

set -e

echo "Downloading CEF directly..."

# Create third_party directory
mkdir -p third_party
cd third_party

# Remove existing cef if it exists
if [ -d "cef" ]; then
    echo "Removing existing CEF..."
    rm -rf cef
fi

# Use a specific known working version
CEF_VERSION="119.4.7+g55e15c8+chromium-119.0.6045.199"
CEF_FILE="cef_binary_${CEF_VERSION}_macosx64.tar.bz2"

echo "Downloading CEF $CEF_VERSION..."

# Try curl first, then wget
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$CEF_FILE" "https://cef-builds.spotifycdn.com/$CEF_FILE" || \
    curl -L -o "$CEF_FILE" "https://github.com/chromiumembedded/cef/releases/download/119.4.7%2Bg55e15c8%2Bchromium-119.0.6045.199/$CEF_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget "https://cef-builds.spotifycdn.com/$CEF_FILE" || \
    wget "https://github.com/chromiumembedded/cef/releases/download/119.4.7%2Bg55e15c8%2Bchromium-119.0.6045.199/$CEF_FILE"
else
    echo "ERROR: Neither curl nor wget found. Please install one of them."
    exit 1
fi

echo "Extracting CEF..."
tar -xjf "$CEF_FILE"

# Get the extracted directory name
dirname=$(tar -tf "$CEF_FILE" | head -1 | cut -f1 -d"/")
mv "$dirname" cef

# Cleanup
rm "$CEF_FILE"

# Build CEF wrapper library
cd cef
mkdir -p build
cd build

echo "Building CEF wrapper library..."
cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release ..
make -j$(sysctl -n hw.ncpu) libcef_dll_wrapper

cd ../..
cd ..

echo "CEF setup completed successfully!"
echo "CEF installed to: third_party/cef/"