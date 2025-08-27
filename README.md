# Screen Capture Tiling System

A high-performance screen capture system that uses mixed VP9/H.264 tiling with hardware acceleration, built with C++, Ray, FastAPI, and WebAssembly.

## Architecture

- **C++ Backend**: CEF-based screen capture with real VP9/H.264 encoders
- **Ray FastAPI Server**: Distributed tile processing with WebSocket communication  
- **WASM Decoder**: Client-side tile decoding for canvas rendering
- **Web Interface**: Real-time display with tile visualization

## Features

- **Mixed Codec Tiling**: VP9 for static areas, H.264 for motion areas (128x128 tiles)
- **Hardware Acceleration**: Real libvpx and x264 encoders
- **Zero-Copy Memory**: Optimized data transfers
- **Real-time Processing**: 30+ FPS with low latency
- **Distributed Processing**: Ray actors for parallel tile encoding

## Dependencies

### System Requirements
- CEF (Chromium Embedded Framework)
- libvpx (VP9 codec)
- x264 (H.264 codec)  
- FFmpeg (libavcodec, libavformat, libavutil, libswscale)
- Emscripten (for WASM build)
- Ray and FastAPI (Python)

### Installation

#### macOS (Homebrew)
```bash
brew install libvpx x264 ffmpeg pkg-config
```

#### Ubuntu/Debian
```bash
sudo apt-get install libvpx-dev libx264-dev libavcodec-dev libavformat-dev libavutil-dev libswscale-dev pkg-config
```

#### Python Dependencies
```bash
pip install -r requirements.txt
```

## Building

```bash
./build.sh
```

This will:
1. Build the C++ screen capture executable
2. Compile the WASM decoder module
3. Copy WASM files to the web directory

## Running

### 1. Start the Ray FastAPI Server
```bash
python src/websocket_server.py
```

### 2. Start the C++ Screen Capture
```bash
./build/screen_capture
```

### 3. Open Web Interface
Navigate to: http://localhost:8000

## Usage

1. Click "Start Screen Capture" in the web interface
2. Select screen/window to capture
3. View real-time tiled rendering with codec visualization:
   - Green borders: VP9 tiles (static areas)
   - Red borders: H.264 tiles (motion areas)

## Technical Details

### Tile Processing Pipeline
1. **CEF Capture**: WebRTC screen capture → raw BGRA frames
2. **Motion Detection**: Per-tile analysis for codec selection
3. **Encoding**: Parallel VP9/H.264 encoding via Ray actors
4. **WebSocket**: Binary tile data transmission
5. **WASM Decode**: Client-side VP9/H.264 decoding
6. **Canvas Render**: Reconstructed frame display

### Performance Optimizations
- Hardware-accelerated encoding (NVENC/Quick Sync when available)
- Zero-copy memory transfers
- Parallel tile processing via Ray
- Efficient BGRA↔I420 color space conversion
- WebSocket binary protocol

### Codec Selection Logic
- **VP9**: Static tiles (< 5% pixel change)
- **H.264**: Motion tiles (≥ 5% pixel change)
- Per-tile motion detection using frame differencing

## File Structure

```
├── src/
│   ├── main.cpp                 # C++ application entry point
│   ├── screen_capture_handler.* # CEF screen capture integration
│   ├── tiled_encoder.*          # VP9/H.264 tile encoding
│   ├── wasm_decoder.cpp         # WebAssembly decoder module
│   └── websocket_server.py      # Ray FastAPI WebSocket server
├── web/
│   ├── index.html              # Web interface
│   └── main.js                 # JavaScript client logic
├── include/
│   └── *.h                     # C++ header files
├── CMakeLists.txt              # Build configuration
├── build.sh                   # Build script
└── requirements.txt           # Python dependencies
```

## License

MIT License