#!/usr/bin/env python3
"""
Test server startup and basic functionality.
"""

import sys
import os
import time
import threading
import requests

# Add src to path
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')

def test_server_startup():
    """Test server startup."""
    print("=== Testing Server Startup ===")
    
    try:
        from websocket_server import app
        import uvicorn
        
        def run_server():
            try:
                uvicorn.run(app, host="127.0.0.1", port=8002, log_level="critical")
            except Exception as e:
                print(f"Server error: {e}")
        
        # Start server in background
        print("Starting server...")
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Give server time to start
        time.sleep(3)
        
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://localhost:8002/health", timeout=5)
        health_data = response.json()
        
        print(f"✓ Health check successful:")
        print(f"  Status: {health_data['status']}")
        print(f"  CEF initialized: {health_data['cef_initialized']}")
        print(f"  Streaming active: {health_data['streaming_active']}")
        print(f"  Connections: {health_data['connections']}")
        
        # Test main page
        print("Testing main page...")
        main_response = requests.get("http://localhost:8002/", timeout=5)
        print(f"✓ Main page accessible (status: {main_response.status_code})")
        
        return True
        
    except Exception as e:
        print(f"✗ Server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🌐 Server Startup Test")
    print("=" * 30)
    
    success = test_server_startup()
    
    print("\n" + "=" * 30)
    if success:
        print("✅ Server startup test passed!")
        print("\n🚀 Ready to run the full server:")
        print("  cd /Users/andrewgrosser/Documents/scap")
        print("  source .venv/bin/activate") 
        print("  DYLD_FRAMEWORK_PATH=tests python src/websocket_server.py")
    else:
        print("❌ Server startup failed")