# CEF Build Instructions for Claude

## Prerequisites
```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements_simple.txt
```

## Build Process
```bash
# 1. Download correct architecture CEF
./download_cef_direct.sh

# 2. Build the simple_cef Python module
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make simple_cef

# 3. Fix library paths and code signing (macOS)
install_name_tool -change "@executable_path/../Frameworks/Chromium Embedded Framework.framework/Chromium Embedded Framework" "@loader_path/Chromium Embedded Framework.framework/Chromium Embedded Framework" simple_cef*.so

# 4. Sign the binaries
codesign --force --sign - simple_cef*.so
codesign --force --sign - ../Chromium\ Embedded\ Framework.framework/Chromium\ Embedded\ Framework

# 5. Copy to project root
cp simple_cef*.so ../
cp -r ../third_party/cef/Release/Chromium\ Embedded\ Framework.framework ../

# 6. Generate protobuf files
protoc --python_out=src src/frame_data.proto
```

## Running
```bash
# Start server
source .venv/bin/activate
DYLD_FRAMEWORK_PATH=. python src/websocket_server.py

# Or use start script
python start_server.py
```

## Troubleshooting

### Code signing issues on macOS:
```bash
# Re-sign all CEF components
codesign --force --sign - Chromium\ Embedded\ Framework.framework/Chromium\ Embedded\ Framework
codesign --force --sign - simple_cef.cpython-*-darwin.so
```

### Library path issues:
```bash
# Check current paths
otool -L simple_cef*.so

# Fix CEF framework path
install_name_tool -change "@executable_path/../Frameworks/..." "@loader_path/..." simple_cef*.so
```

### Build dependencies:
```bash
# Install required tools
brew install cmake protobuf pkg-config

# Install Python deps
uv pip install pybind11 numpy pillow fastapi uvicorn websockets av protobuf
```

## Architecture Detection
The `download_cef_direct.sh` script automatically detects:
- Apple Silicon (ARM64) → downloads `macosarm64` version
- Intel (x86_64) → downloads `macosx64` version

## Performance Settings
- Resolution: 900x600 (configurable)
- Tile size: 112x112 (configurable) 
- Frame rate: 10 FPS backend (configurable)
- Compression: zlib level 1 (fast)
- Protocol: Binary protobuf (~12KB vs 14MB JSON)