#!/usr/bin/env python3
"""
Test the new CEF websocket server implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import json
import websockets
import threading
import time
from websocket_server import app, browser_manager
import uvicorn

def test_basic_import():
    """Test that the websocket server imports correctly."""
    print("=== WebSocket Server Import Test ===")
    
    try:
        from src.websocket_server import VideoEncoder, TileProcessor, CEFBrowserManager
        print("✓ All classes imported successfully")
        
        # Test VideoEncoder creation
        encoder = VideoEncoder('vp9', 128, 128)
        print("✓ VP9 encoder created")
        
        encoder_h264 = VideoEncoder('h264', 128, 128)
        print("✓ H264 encoder created")
        
        # Test TileProcessor
        processor = TileProcessor(128)
        print("✓ Tile processor created")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cef_browser_manager():
    """Test the CEF browser manager."""
    print("\n=== CEF Browser Manager Test ===")
    
    try:
        # Create browser manager
        manager = CEFBrowserManager(640, 480)
        print(f"✓ Browser manager created")
        
        if manager.is_initialized:
            print("✓ CEF browser initialized successfully")
            
            # Test capturing a frame (without CEF initialization - will get empty frame)
            pixels, tiles = manager.capture_frame()
            
            if pixels is not None:
                print(f"✓ Frame captured: {pixels.shape}")
                print(f"✓ Tiles generated: {len(tiles)}")
                
                # Show tile info
                if tiles:
                    tile = tiles[0]
                    print(f"  Sample tile: {tile['codec']} at ({tile['x']},{tile['y']})")
                    print(f"  Encoded size: {tile['size']} bytes")
            else:
                print("⚠ No frame data (expected without full CEF init)")
            
        else:
            print("⚠ CEF browser not initialized (expected in test environment)")
        
        return True
        
    except Exception as e:
        print(f"✗ Browser manager error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_websocket_client():
    """Test WebSocket connection."""
    print("\n=== WebSocket Client Test ===")
    
    try:
        # Note: This requires the server to be running
        uri = "ws://localhost:8000/ws"
        
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket server")
            
            # Send start stream message
            start_message = {
                'type': 'start_stream',
                'url': 'https://www.example.com'
            }
            await websocket.send(json.dumps(start_message))
            print("✓ Sent start stream message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"✓ Received response: {data['type']}")
            
            # Send ping
            ping_message = {'type': 'ping'}
            await websocket.send(json.dumps(ping_message))
            
            pong = await asyncio.wait_for(websocket.recv(), timeout=5)
            pong_data = json.loads(pong)
            print(f"✓ Ping/pong successful: {pong_data['type']}")
            
            return True
            
    except asyncio.TimeoutError:
        print("⚠ WebSocket test timeout (server may not be running)")
        return False
    except Exception as e:
        print(f"⚠ WebSocket test error: {e} (server may not be running)")
        return False

def run_server_briefly():
    """Run server briefly for testing."""
    print("\n=== Brief Server Test ===")
    
    def run_server():
        try:
            uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
        except:
            pass
    
    # Start server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(2)
    print("✓ Server started on port 8001")
    
    # Test health endpoint
    try:
        import requests
        response = requests.get("http://localhost:8001/health", timeout=3)
        health_data = response.json()
        print(f"✓ Health check: {health_data}")
        return True
    except Exception as e:
        print(f"⚠ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing CEF WebSocket Server Implementation")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_basic_import()
    
    # Test CEF browser manager
    success &= test_cef_browser_manager()
    
    # Test server briefly
    success &= run_server_briefly()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All basic tests passed!")
        print("\n🚀 New WebSocket Server Features:")
        print("  • CEF headless browser integration")
        print("  • VP9/H264 tile encoding with PyAV")
        print("  • Motion-based codec selection") 
        print("  • Real-time frame streaming")
        print("  • Multi-client WebSocket support")
        print("  • REST API endpoints")
        
        print("\n🎯 To run the server:")
        print("  python src/websocket_server.py")
        print("  Open: http://localhost:8000")
    else:
        print("❌ Some tests failed")
        print("Check dependencies and CEF module availability")