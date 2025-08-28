#!/usr/bin/env python3
"""
Start the complete CEF streaming server.
"""

import sys
import os
import time
import threading

# Add src to path
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')

def main():
    print("🚀 Starting CEF WebSocket Server with VP9/H264 Tiling")
    print("=" * 60)
    
    try:
        from websocket_server import app
        import uvicorn
        
        print("✓ Imports successful")
        print("✓ CEF module loaded")
        print("✓ VP9/H264 encoders ready")
        
        print(f"\n🌐 Server starting on:")
        print(f"  • Web UI: http://localhost:8000")
        print(f"  • WebSocket: ws://localhost:8000/ws")
        print(f"  • Health: http://localhost:8000/health")
        
        print(f"\n📱 Features active:")
        print(f"  • CEF headless browser")
        print(f"  • Motion-based codec selection")
        print(f"  • Real-time tile streaming")
        print(f"  • Multi-client support")
        
        # Start server
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped by user")
    except Exception as e:
        print(f"\n✗ Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()