#!/usr/bin/env python3
"""
Basic test for the new websocket server.
"""

import sys
import os

# Add src to path
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')

def test_imports():
    """Test basic imports."""
    print("=== Testing WebSocket Server Imports ===")
    
    try:
        # Test individual imports
        print("Testing imports...")
        
        import simple_cef
        print("✓ simple_cef imported")
        
        from websocket_server import VideoEncoder
        print("✓ VideoEncoder imported")
        
        from websocket_server import TileProcessor  
        print("✓ TileProcessor imported")
        
        from websocket_server import CEFBrowserManager
        print("✓ CEFBrowserManager imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_encoder():
    """Test video encoder creation."""
    print("\n=== Testing Video Encoders ===")
    
    try:
        from websocket_server import VideoEncoder
        
        # Test VP9 encoder
        vp9_encoder = VideoEncoder('vp9', 128, 128)
        print("✓ VP9 encoder created")
        
        # Test H264 encoder
        h264_encoder = VideoEncoder('h264', 128, 128)
        print("✓ H264 encoder created")
        
        # Test encoding with dummy data
        import numpy as np
        dummy_tile = np.zeros((128, 128, 4), dtype=np.uint8)
        
        encoded_vp9 = vp9_encoder.encode_tile(dummy_tile)
        print(f"✓ VP9 encoding: {len(encoded_vp9)} bytes")
        
        encoded_h264 = h264_encoder.encode_tile(dummy_tile)
        print(f"✓ H264 encoding: {len(encoded_h264)} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Video encoder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tile_processor():
    """Test tile processor."""
    print("\n=== Testing Tile Processor ===")
    
    try:
        from websocket_server import TileProcessor
        import numpy as np
        
        processor = TileProcessor(128)
        print("✓ Tile processor created")
        
        # Create dummy tile data
        tile_data = np.random.randint(0, 255, (64, 64, 4), dtype=np.uint8)
        
        # Process tile
        result = processor.process_tile(tile_data, 0, 0, 1)
        print(f"✓ Tile processed: {result['codec']} codec")
        print(f"  Motion detected: {result['has_motion']}")
        print(f"  Encoded size: {result['size']} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Tile processor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cef_manager():
    """Test CEF browser manager creation."""
    print("\n=== Testing CEF Manager ===")
    
    try:
        from websocket_server import CEFBrowserManager
        
        # Create manager (this will try to init CEF)
        manager = CEFBrowserManager(640, 480)
        print("✓ CEF manager created")
        
        print(f"  Initialized: {manager.is_initialized}")
        print(f"  Current URL: {manager.current_url}")
        
        return True
        
    except Exception as e:
        print(f"✗ CEF manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Basic WebSocket Server Tests")
    print("=" * 40)
    
    success = True
    
    success &= test_imports()
    success &= test_video_encoder() 
    success &= test_tile_processor()
    success &= test_cef_manager()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All basic tests passed!")
        print("\n🎉 New WebSocket Server Ready:")
        print("  • CEF headless browser ✓")
        print("  • VP9/H264 encoding ✓") 
        print("  • Tile processing ✓")
        print("  • Motion detection ✓")
    else:
        print("❌ Some tests failed")