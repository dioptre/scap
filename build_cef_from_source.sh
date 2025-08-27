#!/bin/bash

# Build CEF from source using automate-git.py
# Warning: This takes several hours and requires 40+ GB disk space

set -e

echo "Building CEF from source (this will take several hours)..."

source .venv/bin/activate

# Download automate-git.py
mkdir -p third_party
cd third_party

if [ ! -f "automate-git.py" ]; then
    curl -o automate-git.py https://bitbucket.org/chromiumembedded/cef/raw/master/tools/automate/automate-git.py
    chmod +x automate-git.py
fi


# Build CEF (customize branch/version as needed)
python automate-git.py \
    --download-dir=cef_source \
    --depot-tools-dir=depot_tools \
    --branch=5563 \
    --minimal-distrib \
    --client-distrib \
    --build-target=cefclient \
    --arm64-build

echo "CEF source build completed!"
echo "CEF binaries are in: third_party/cef_source/chromium/src/cef/binary_distrib/"

# Find the built CEF distribution
CEF_DISTRIB_DIR=$(find cef_source/chromium/src/cef/binary_distrib/ -name "*macosx64*" -type d | head -1)

if [ -n "$CEF_DISTRIB_DIR" ]; then
    echo "Found CEF distribution: $CEF_DISTRIB_DIR"
    
    # Create symlink for easy access
    if [ -L "cef" ]; then
        rm cef
    elif [ -d "cef" ]; then
        rm -rf cef
    fi
    
    ln -s "$CEF_DISTRIB_DIR" cef
    echo "Created symlink: cef -> $CEF_DISTRIB_DIR"
    
    # Build the wrapper library
    cd cef
    mkdir -p build
    cd build
    cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release ..
    make -j$(sysctl -n hw.ncpu) libcef_dll_wrapper
    cd ../..
else
    echo "ERROR: Could not find CEF distribution directory"
    exit 1
fi

cd ..