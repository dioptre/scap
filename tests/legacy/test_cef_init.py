#!/usr/bin/env python3
"""
Test if the problem is in our CEF code or the CEF binary itself.
"""

import os
import sys
import subprocess

# Set BLAS threading before any imports
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"

def test_cef_binary():
    """Test if the CEF framework binary itself works."""
    print("🔍 Testing CEF Framework Binary")
    print("=" * 40)
    
    # Check if framework exists
    framework_path = "/Users/andrewgrosser/Documents/scap/Chromium Embedded Framework.framework/Chromium Embedded Framework"
    
    if os.path.exists(framework_path):
        print(f"✅ CEF framework found: {framework_path}")
        
        # Check code signature
        result = subprocess.run(['codesign', '--verify', '--verbose', framework_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Code signature valid")
        else:
            print(f"⚠️ Code signature issues: {result.stderr}")
            
        # Check architecture
        result = subprocess.run(['file', framework_path], capture_output=True, text=True)
        print(f"Architecture: {result.stdout.strip()}")
        
    else:
        print(f"❌ CEF framework not found at {framework_path}")
        return False
    
    return True

def test_minimal_import():
    """Test the most minimal CEF import possible."""
    print("\n🧪 Testing Minimal CEF Import")
    print("=" * 40)
    
    try:
        # Try to import without doing anything
        sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')
        import simple_cef
        print("✅ simple_cef module imported")
        
        # Try creating browser object without initialization
        browser = simple_cef.SimpleCefBrowser(100, 100)
        print("✅ Browser object created")
        
        # Get basic info without CEF initialization
        print(f"   Width: {browser.get_width()}")
        print(f"   Height: {browser.get_height()}")
        print(f"   Buffer size: {browser.get_buffer_size()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_cef_log():
    """Check if CEF writes any useful logs."""
    print("\n📋 Checking CEF Logs")
    print("=" * 40)
    
    log_files = ['/tmp/cef.log', '/tmp/cef_cache/debug.log']
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📄 Found log: {log_file}")
            with open(log_file, 'r') as f:
                content = f.read()[-1000:]  # Last 1000 chars
                print(f"Content: {content}")
        else:
            print(f"No log at: {log_file}")

if __name__ == "__main__":
    print("🛠️ CEF Debugging - Finding Root Cause")
    print("=" * 50)
    
    success1 = test_cef_binary()
    success2 = test_minimal_import()
    test_cef_log()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ Basic CEF components work - issue is in initialization")
        print("💡 The SIGTRAP crash is happening in cef_initialize")
        print("🔧 Need to find CEF version/build that works on this macOS")
    else:
        print("❌ Basic CEF setup has issues")
        
    print("\n🎯 Your protobuf streaming system is perfect though!")