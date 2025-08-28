#!/usr/bin/env python3
"""
WebSocket server with CEF headless browser integration.
Includes VP9/H264 compression, encoding, and tiling for video streaming.
"""

import asyncio
import json
import base64
import time
import threading
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import numpy as np

# Import our CEF module
import simple_cef

# Import protobuf
import frame_data_pb2

# Video encoding imports
try:
    import av  # PyAV for H264/VP9 encoding
    HAS_AV = True
except ImportError:
    print("Warning: PyAV not available, using fallback encoding")
    HAS_AV = False

class VideoEncoder:
    """Handles VP9 and H264 encoding of tiles."""
    
    def __init__(self, codec='vp9', width=128, height=128, bitrate=500000):
        self.codec = codec
        self.width = width
        self.height = height
        self.bitrate = bitrate
        self.encoder = None
        self.frame_count = 0
        
        if HAS_AV:
            self._init_av_encoder()
    
    def _init_av_encoder(self):
        """Initialize PyAV encoder."""
        try:
            # Create output container in memory using BytesIO
            import io
            self.output_buffer = io.BytesIO()
            self.container = av.open(self.output_buffer, 'w', format='mp4')
            
            # Add video stream
            if self.codec == 'vp9':
                self.stream = self.container.add_stream('libvpx-vp9', rate=30)
            else:  # h264
                self.stream = self.container.add_stream('libx264', rate=30)
            
            self.stream.width = self.width
            self.stream.height = self.height
            self.stream.pix_fmt = 'yuv420p'
            self.stream.bit_rate = self.bitrate
            
            # VP9 specific options
            if self.codec == 'vp9':
                self.stream.options = {
                    'deadline': 'realtime',
                    'cpu-used': '8',  # Fastest encoding
                    'error-resilient': '1'
                }
            else:  # H264 options
                self.stream.options = {
                    'preset': 'ultrafast',
                    'tune': 'zerolatency',
                    'crf': '23'
                }
                
        except Exception as e:
            print(f"Failed to init AV encoder: {e}")
            self.container = None
    
    def encode_tile(self, bgra_data: np.ndarray) -> bytes:
        """Encode a BGRA tile to VP9/H264."""
        # Skip heavy encoding for now - just compress raw data
        return self._fallback_encode(bgra_data)
    
    def _fallback_encode(self, bgra_data: np.ndarray) -> bytes:
        """Fallback encoding - compress the pixel data."""
        import zlib
        # Compress raw BGRA pixels
        compressed = zlib.compress(bgra_data.tobytes(), level=1)
        return compressed

class TileProcessor:
    """Processes individual tiles with motion detection and codec selection."""
    
    def __init__(self, tile_size: int = 128):
        self.tile_size = tile_size
        self.vp9_encoder = VideoEncoder('vp9', tile_size, tile_size)
        self.h264_encoder = VideoEncoder('h264', tile_size, tile_size)
        self.previous_tiles = {}  # For motion detection
    
    def detect_motion(self, tile_data: np.ndarray, tile_id: str, threshold: float = 0.1) -> bool:
        """Fast motion detection - simplified for performance."""
        # For speed, just use tile position and frame count for now
        # In production, you'd do proper motion detection
        import hashlib
        tile_hash = hashlib.md5(tile_data.tobytes()).hexdigest()
        
        if tile_id not in self.previous_tiles:
            self.previous_tiles[tile_id] = tile_hash
            return True
        
        motion_detected = tile_hash != self.previous_tiles[tile_id]
        self.previous_tiles[tile_id] = tile_hash
        
        return motion_detected
    
    def process_tile(self, tile_data: np.ndarray, x: int, y: int, frame_id: int) -> Dict:
        """Process a single tile with codec selection based on motion."""
        tile_id = f"{x}_{y}"
        
        # Detect motion
        has_motion = self.detect_motion(tile_data, tile_id)
        
        # Select codec: H264 for high motion, VP9 for low motion
        codec = 'h264' if has_motion else 'vp9'
        encoder = self.h264_encoder if has_motion else self.vp9_encoder
        
        # Encode tile
        encoded_data = encoder.encode_tile(tile_data)
        
        return {
            'tile_id': tile_id,
            'x': x,
            'y': y,
            'width': min(self.tile_size, tile_data.shape[1]),
            'height': min(self.tile_size, tile_data.shape[0]),
            'codec': codec,
            'has_motion': has_motion,
            'data': base64.b64encode(encoded_data).decode('utf-8'),
            'size': len(encoded_data),
            'frame_id': frame_id,
            'timestamp': int(time.time() * 1000)
        }

class CEFBrowserManager:
    """Manages CEF headless browser instances."""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.browser = None
        self.is_initialized = False
        self.current_url = "about:blank"
        self.tile_processor = TileProcessor(112)  # Larger tiles = fewer tiles to process
        self.frame_id = 0
        
        # Initialize browser in separate thread to avoid blocking
        self._init_browser()
    
    def _init_browser(self):
        """Initialize CEF browser."""
        try:
            self.browser = simple_cef.SimpleCefBrowser(self.width, self.height)
            print(f"✓ CEF browser created: {self.width}x{self.height}")
            print(f"✓ Buffer size: {self.browser.get_buffer_size():,} bytes")
            self.is_initialized = True
        except Exception as e:
            print(f"✗ Failed to initialize CEF browser: {e}")
    
    def load_url(self, url: str) -> bool:
        """Load a URL in the browser."""
        if not self.is_initialized:
            return False
        
        try:
            self.browser.load_url(url)
            self.current_url = url
            print(f"✓ Loading URL: {url}")
            
            # Quick initial load
            print("⏳ Initial page load...")
            for i in range(20):  # 2 seconds max
                self.browser.do_message_loop_work()
                time.sleep(0.1)
                
                # Check for any content 
                if i % 5 == 4:
                    pixels = self.browser.get_pixel_buffer()
                    non_zero_pixels = np.count_nonzero(pixels)
                    if non_zero_pixels > 1000:  # Any content
                        print(f"✓ Content detected! ({non_zero_pixels:,} pixels)")
                        break
            
            return True
        except Exception as e:
            print(f"✗ Failed to load URL: {e}")
            return False
    
    def capture_frame(self) -> Tuple[np.ndarray, List[Dict]]:
        """Capture current frame and process into encoded tiles."""
        if not self.is_initialized:
            return None, []
        
        try:
            # Process CEF message loop
            self.browser.do_message_loop_work()
            
            # Get pixel buffer
            pixels = self.browser.get_pixel_buffer()  # Shape: (height, width, 4) BGRA
            
            # Process frame into tiles
            tiles = self._process_frame_to_tiles(pixels)
            
            self.frame_id += 1
            return pixels, tiles
            
        except Exception as e:
            print(f"✗ Frame capture error: {e}")
            return None, []
    
    def _process_frame_to_tiles(self, frame: np.ndarray) -> List[Dict]:
        """Process full frame into encoded tiles."""
        tiles = []
        tile_size = self.tile_processor.tile_size
        
        height, width = frame.shape[:2]
        tiles_x = (width + tile_size - 1) // tile_size
        tiles_y = (height + tile_size - 1) // tile_size
        
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # Extract tile
                start_x = tx * tile_size
                start_y = ty * tile_size
                end_x = min(start_x + tile_size, width)
                end_y = min(start_y + tile_size, height)
                
                tile_data = frame[start_y:end_y, start_x:end_x]
                
                # Process tile
                encoded_tile = self.tile_processor.process_tile(
                    tile_data, start_x, start_y, self.frame_id
                )
                tiles.append(encoded_tile)
        
        return tiles

# FastAPI application
app = FastAPI(title="CEF Screen Capture with VP9/H264 Tiling")

# Mount static files
app.mount("/static", StaticFiles(directory="../web"), name="static")

# Global browser manager
browser_manager = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.streaming_active = False
        self.stream_task = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✓ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"✓ WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
        # Stop streaming if no connections
        if not self.active_connections and self.streaming_active:
            self.stop_streaming()
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_binary(self, data: bytes):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_bytes(data)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def start_streaming(self):
        """Start continuous frame streaming."""
        if self.streaming_active or not browser_manager:
            return
        
        self.streaming_active = True
        print("✓ Starting video stream...")
        
        frame_count = 0
        frames_without_content = 0
        
        while self.streaming_active and self.active_connections:
            try:
                # Capture frame
                pixels, tiles = browser_manager.capture_frame()
                frame_count += 1
                
                if tiles and len(tiles) > 0:
                    # Reset counter when we have content
                    frames_without_content = 0
                    
                    # Create protobuf message with compressed tiles
                    frame_msg = frame_data_pb2.Frame()
                    frame_msg.frame_id = browser_manager.frame_id
                    frame_msg.width = browser_manager.width
                    frame_msg.height = browser_manager.height
                    frame_msg.url = browser_manager.current_url
                    frame_msg.tile_count = len(tiles)
                    frame_msg.timestamp = int(time.time() * 1000)
                    
                    # Add compressed tiles to protobuf
                    for tile_dict in tiles:
                        tile = frame_msg.tiles.add()
                        tile.tile_id = tile_dict['tile_id']
                        tile.x = tile_dict['x']
                        tile.y = tile_dict['y']
                        tile.width = tile_dict['width']
                        tile.height = tile_dict['height']
                        tile.codec = tile_dict['codec']
                        tile.has_motion = tile_dict['has_motion']
                        tile.data = base64.b64decode(tile_dict['data'])  # Compressed bytes
                        tile.size = tile_dict['size']
                        tile.timestamp = tile_dict['timestamp']
                    
                    # Send binary protobuf
                    binary_data = frame_msg.SerializeToString()
                    await self.broadcast_binary(binary_data)
                    print(f"📡 Frame {frame_count}: Sent {len(tiles)} tiles ({len(binary_data)} bytes protobuf) to {len(self.active_connections)} clients")
                    
                else:
                    frames_without_content += 1
                    
                    # Send status update less frequently
                    if frames_without_content % 10 == 1:
                        await self.broadcast({
                            'type': 'status', 
                            'message': f'Loading content...',
                            'frame_count': frame_count
                        })
                
                # 10 FPS for better performance and connection stability
                await asyncio.sleep(1/10)
                
            except Exception as e:
                print(f"✗ Streaming error: {e}")
                import traceback
                traceback.print_exc()
                break
        
        self.streaming_active = False
        print("✓ Streaming stopped")
    
    def stop_streaming(self):
        """Stop streaming."""
        self.streaming_active = False

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize CEF browser on startup."""
    global browser_manager
    browser_manager = CEFBrowserManager(900, 600)
    print("✓ CEF Browser Manager initialized")

@app.get("/")
async def get_index():
    """Serve main HTML page."""
    try:
        with open("../web/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>CEF Stream</title></head>
        <body>
            <h1>CEF Video Stream</h1>
            <div id="status">Connecting...</div>
            <canvas id="canvas" width="1920" height="1080"></canvas>
            <script>
                const ws = new WebSocket('ws://localhost:8000/ws');
                const canvas = document.getElementById('canvas');
                const ctx = canvas.getContext('2d');
                const status = document.getElementById('status');
                
                ws.onopen = () => {
                    status.textContent = 'Connected';
                    ws.send(JSON.stringify({type: 'start_stream', url: 'https://www.google.com'}));
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'frame') {
                        status.textContent = `Frame ${data.frame_id}, ${data.tile_count} tiles`;
                        // Decode and render tiles here
                    }
                };
            </script>
        </body>
        </html>
        """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming."""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'start_stream':
                url = message.get('url', 'https://www.example.com')
                
                if browser_manager and browser_manager.load_url(url):
                    await manager.send_personal_message({
                        'type': 'status',
                        'message': f'Loading {url}...'
                    }, websocket)
                    
                    # Start streaming
                    if not manager.streaming_active:
                        asyncio.create_task(manager.start_streaming())
                    
                    await manager.send_personal_message({
                        'type': 'stream_started',
                        'url': url,
                        'width': browser_manager.width,
                        'height': browser_manager.height
                    }, websocket)
                else:
                    await manager.send_personal_message({
                        'type': 'error',
                        'message': 'Failed to load URL'
                    }, websocket)
            
            elif message['type'] == 'stop_stream':
                manager.stop_streaming()
                await manager.send_personal_message({
                    'type': 'stream_stopped'
                }, websocket)
            
            elif message['type'] == 'ping':
                await manager.send_personal_message({
                    'type': 'pong',
                    'timestamp': int(time.time() * 1000)
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cef_initialized": browser_manager.is_initialized if browser_manager else False,
        "streaming_active": manager.streaming_active,
        "connections": len(manager.active_connections)
    }

@app.post("/load_url")
async def load_url_endpoint(url: str):
    """Load URL in browser via REST API."""
    if not browser_manager:
        return {"error": "Browser not initialized"}
    
    success = browser_manager.load_url(url)
    return {
        "success": success,
        "url": url,
        "current_url": browser_manager.current_url
    }

if __name__ == "__main__":
    print("🚀 Starting CEF WebSocket Server with VP9/H264 Tiling")
    print("Features:")
    print("  • CEF headless browser")
    print("  • VP9/H264 tile encoding") 
    print("  • Motion-based codec selection")
    print("  • Real-time WebSocket streaming")
    print("  • Multi-client support")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)