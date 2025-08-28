#!/usr/bin/env python3
"""
Start server directly from src/websocket_server.py
"""

import sys
import os
import subprocess

def main():
    print("🚀 Starting CEF WebSocket Server")
    print("=" * 40)
    
    # Run the server directly 
    cmd = [
        "python", 
        "src/websocket_server.py"
    ]
    
    env = os.environ.copy()
    env['DYLD_FRAMEWORK_PATH'] = '.'
    
    print("Starting server...")
    print("Visit: http://localhost:8000")
    
    try:
        subprocess.run(cmd, env=env, cwd='/Users/andrewgrosser/Documents/scap')
    except KeyboardInterrupt:
        print("\n✓ Server stopped")

if __name__ == "__main__":
    main()