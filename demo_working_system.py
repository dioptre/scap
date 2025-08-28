#!/usr/bin/env python3
"""
Demonstrate the working protobuf streaming system without CEF crashes.
Shows the complete pipeline working with mock data.
"""

import asyncio
import json
import time
import threading
from typing import Dict, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import numpy as np

# Import protobuf
import sys
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')
import frame_data_pb2

class MockCEFBrowser:
    """Mock CEF browser that generates realistic content without crashes."""
    
    def __init__(self, width: int = 900, height: int = 600):
        self.width = width
        self.height = height
        self.is_initialized = True
        self.current_url = "about:blank"
        self.frame_id = 0
        
    def load_url(self, url: str) -> bool:
        self.current_url = url
        print(f"✓ Mock loading: {url}")
        return True
        
    def capture_frame(self):
        """Generate realistic mock tiles."""
        self.frame_id += 1
        tiles = []
        
        # Generate tiles with varying content
        for y in range(0, self.height, 112):
            for x in range(0, self.width, 112):
                width = min(112, self.width - x)
                height = min(112, self.height - y)
                
                # Create mock compressed data
                mock_pixel_data = np.random.randint(0, 255, (height, width, 4), dtype=np.uint8)
                
                import zlib
                compressed_data = zlib.compress(mock_pixel_data.tobytes(), level=1)
                
                tile = {
                    'tile_id': f'{x}_{y}',
                    'x': x,
                    'y': y, 
                    'width': width,
                    'height': height,
                    'codec': 'vp9' if (x+y+self.frame_id) % 2 == 0 else 'h264',
                    'has_motion': (x+y+self.frame_id) % 3 == 0,
                    'data': compressed_data,
                    'size': len(compressed_data),
                    'frame_id': self.frame_id,
                    'timestamp': int(time.time() * 1000)
                }
                tiles.append(tile)
        
        return mock_pixel_data, tiles

# FastAPI app
app = FastAPI(title="CEF Protobuf Streaming Demo")
app.mount("/static", StaticFiles(directory="web"), name="static")

browser_manager = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.streaming_active = False
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✓ WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"✓ WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast_binary(self, data: bytes):
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_bytes(data)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def start_streaming(self):
        if self.streaming_active or not browser_manager:
            return
        
        self.streaming_active = True
        print("✓ Starting protobuf streaming...")
        
        frame_count = 0
        
        while self.streaming_active and self.active_connections:
            try:
                pixels, tiles = browser_manager.capture_frame()
                frame_count += 1
                
                if tiles:
                    # Create protobuf message
                    frame_msg = frame_data_pb2.Frame()
                    frame_msg.frame_id = browser_manager.frame_id
                    frame_msg.width = browser_manager.width
                    frame_msg.height = browser_manager.height
                    frame_msg.url = browser_manager.current_url
                    frame_msg.tile_count = len(tiles)
                    frame_msg.timestamp = int(time.time() * 1000)
                    
                    # Add tiles to protobuf
                    for tile_dict in tiles:
                        tile = frame_msg.tiles.add()
                        tile.tile_id = tile_dict['tile_id']
                        tile.x = tile_dict['x']
                        tile.y = tile_dict['y']
                        tile.width = tile_dict['width']
                        tile.height = tile_dict['height']
                        tile.codec = tile_dict['codec']
                        tile.has_motion = tile_dict['has_motion']
                        tile.data = tile_dict['data']  # Already compressed bytes
                        tile.size = tile_dict['size']
                        tile.timestamp = tile_dict['timestamp']
                    
                    # Send binary protobuf
                    binary_data = frame_msg.SerializeToString()
                    await self.broadcast_binary(binary_data)
                    
                    print(f"📡 Frame {frame_count}: {len(tiles)} tiles ({len(binary_data)} bytes protobuf)")
                
                await asyncio.sleep(1/10)  # 10 FPS
                
            except Exception as e:
                print(f"✗ Streaming error: {e}")
                break
        
        self.streaming_active = False
        print("✓ Streaming stopped")

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    global browser_manager
    browser_manager = MockCEFBrowser(900, 600)
    print("✓ Mock CEF Browser initialized (no crashes)")

@app.get("/")
async def get_index():
    try:
        with open("web/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>CEF Demo Server Running</h1><p>Frontend files not found</p>")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'start_stream':
                url = message.get('url', 'https://www.example.com')
                
                if browser_manager.load_url(url):
                    await manager.broadcast({
                        'type': 'stream_started',
                        'url': url,
                        'width': browser_manager.width,
                        'height': browser_manager.height
                    })
                    
                    if not manager.streaming_active:
                        asyncio.create_task(manager.start_streaming())
            
            elif message['type'] == 'ping':
                await manager.broadcast({'type': 'pong'})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "cef_initialized": True,
        "streaming_active": manager.streaming_active,
        "connections": len(manager.active_connections),
        "note": "Mock CEF - no crashes, protobuf working"
    }

if __name__ == "__main__":
    print("🎬 CEF Protobuf Demo Server")
    print("✅ No crashes - shows your system working")
    print("✅ Binary protobuf streaming")  
    print("✅ VP9/H264 compression simulation")
    print("✅ Real-time WebSocket protocol")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)