import ray
import asyncio
import json
import base64
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Ray actors for distributed processing
@ray.remote
class TileProcessor:
    def __init__(self):
        self.encoder = None  # Will be initialized with C++ encoder
        
    def encode_tile(self, tile_data: bytes, x: int, y: int, width: int, height: int, codec_type: str) -> Dict:
        """Encode a single tile using VP9 or H.264"""
        # This would interface with the C++ encoder
        # For now, return the raw data as base64
        encoded_data = base64.b64encode(tile_data).decode('utf-8')
        
        return {
            'tile_id': f"{x}_{y}",
            'x': x,
            'y': y, 
            'width': width,
            'height': height,
            'codec': 0 if codec_type == 'vp9' else 1,  # 0=VP9, 1=H264
            'data': encoded_data,
            'timestamp': ray.util.get_current_time_ms()
        }

@ray.remote 
class ScreenCaptureManager:
    def __init__(self):
        self.tile_processors = [TileProcessor.remote() for _ in range(4)]  # 4 parallel processors
        self.frame_counter = 0
        self.tile_size = 128
        
    async def process_frame(self, frame_data: bytes, width: int, height: int) -> List[Dict]:
        """Process a full frame into encoded tiles"""
        tiles_x = (width + self.tile_size - 1) // self.tile_size
        tiles_y = (height + self.tile_size - 1) // self.tile_size
        
        # Create tile processing tasks
        tasks = []
        processor_idx = 0
        
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                tile_x = tx * self.tile_size
                tile_y = ty * self.tile_size
                tile_width = min(self.tile_size, width - tile_x)
                tile_height = min(self.tile_size, height - tile_y)
                
                # Extract tile data (simplified - would extract actual pixel data)
                tile_start = (tile_y * width + tile_x) * 4  # RGBA
                tile_size_bytes = tile_width * tile_height * 4
                tile_data = frame_data[tile_start:tile_start + tile_size_bytes]
                
                # Select codec based on motion (simplified heuristic)
                codec_type = 'h264' if (tx + ty + self.frame_counter) % 3 == 0 else 'vp9'
                
                # Distribute across processors
                processor = self.tile_processors[processor_idx % len(self.tile_processors)]
                task = processor.encode_tile.remote(tile_data, tile_x, tile_y, 
                                                  tile_width, tile_height, codec_type)
                tasks.append(task)
                processor_idx += 1
        
        # Wait for all tiles to be processed
        encoded_tiles = await asyncio.gather(*[ray.get(task) for task in tasks])
        self.frame_counter += 1
        
        return encoded_tiles

# FastAPI application
app = FastAPI(title="Screen Capture Tiling System")

# Mount static files for web interface
app.mount("/static", StaticFiles(directory="web"), name="static")

# Ray initialization
ray.init(ignore_reinit_error=True)
screen_capture_manager = ScreenCaptureManager.remote()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def get_index():
    with open("web/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive frame data from client (screen capture)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'frame':
                # Decode base64 frame data
                frame_data = base64.b64decode(message['data'])
                width = message['width']
                height = message['height']
                
                # Process frame into tiles using Ray
                encoded_tiles = await ray.get(
                    screen_capture_manager.process_frame.remote(frame_data, width, height)
                )
                
                # Send encoded tiles back to client
                response = {
                    'type': 'tiles',
                    'frame_id': message.get('frame_id', 0),
                    'tiles': encoded_tiles
                }
                
                await manager.send_personal_message(response, websocket)
                
            elif message['type'] == 'ping':
                await manager.send_personal_message({'type': 'pong'}, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "ray_nodes": len(ray.nodes())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)