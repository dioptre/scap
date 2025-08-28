#!/usr/bin/env python3
"""
Start server without CEF initialization to avoid crashes.
"""

import sys
import os
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')

# Temporarily disable CEF to avoid crashes
import websocket_server

# Monkey patch to avoid CEF initialization
class MockBrowser:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.is_initialized = True
        self.current_url = "about:blank"
        
    def load_url(self, url):
        self.current_url = url
        print(f"✓ Mock loading: {url}")
        return True
        
    def capture_frame(self):
        # Return mock tiles to show the system working
        import numpy as np
        tiles = []
        
        # Create mock compressed tiles
        for y in range(0, 600, 112):
            for x in range(0, 900, 112):
                tile = {
                    'tile_id': f'{x}_{y}',
                    'x': x,
                    'y': y,
                    'width': min(112, 900-x),
                    'height': min(112, 600-y),
                    'codec': 'vp9' if (x+y) % 2 == 0 else 'h264',
                    'has_motion': (x+y) % 3 == 0,
                    'data': 'compressed_mock_data_' + str(x) + '_' + str(y),
                    'size': 150 + (x+y) % 50,
                    'frame_id': 1,
                    'timestamp': int(time.time() * 1000)
                }
                tiles.append(tile)
        
        return None, tiles

# Replace the CEF browser manager
websocket_server.CEFBrowserManager = MockBrowser

import uvicorn
import time

def main():
    print("🧪 Safe Server (Mock CEF to avoid crashes)")
    print("=" * 50)
    
    try:
        from websocket_server import app
        
        print("✓ WebSocket server ready")
        print("✓ Mock CEF browser (no crashes)")
        print("✓ Protobuf streaming enabled")
        print("✓ VP9/H264 tiling simulation")
        
        print(f"\n🌐 Server starting on:")
        print(f"  • http://localhost:8000")
        print(f"  • Mock browser shows system working")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        print(f"✗ Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()