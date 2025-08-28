#!/usr/bin/env python3
"""
Simple CEF headless browser test.
Creates a headless browser, loads a URL, and captures raw pixels for streaming.
"""

import time
import numpy as np
from PIL import Image
import simple_cef

def test_simple_browser():
    """Test basic headless browser functionality."""
    
    # Create browser instance (800x600)
    browser = simple_cef.SimpleCefBrowser(800, 600)
    
    try:
        # Initialize CEF
        print("Initializing CEF...")
        if not browser.initialize():
            print("Failed to initialize CEF")
            return False
        
        print(f"Browser created: {browser.get_width()}x{browser.get_height()}")
        
        # Load a simple webpage
        print("Loading webpage...")
        browser.load_url("https://www.google.com")
        
        # Wait for page to load and process CEF events
        print("Processing CEF events...")
        for i in range(100):  # Process events for ~3 seconds
            browser.do_message_loop_work()
            time.sleep(0.03)  # ~30 FPS
        
        # Get pixel buffer as numpy array
        print("Capturing pixels...")
        pixels = browser.get_pixel_buffer()
        print(f"Pixel buffer shape: {pixels.shape}")
        print(f"Pixel buffer dtype: {pixels.dtype}")
        
        # Convert BGRA to RGB for saving
        rgb_pixels = pixels[:, :, [2, 1, 0]]  # BGR -> RGB
        
        # Save screenshot
        img = Image.fromarray(rgb_pixels, 'RGB')
        img.save("test_screenshot.png")
        print("Screenshot saved as test_screenshot.png")
        
        # Print some pixel data for verification
        print(f"Sample pixel values (top-left corner):")
        for y in range(min(5, pixels.shape[0])):
            for x in range(min(5, pixels.shape[1])):
                b, g, r, a = pixels[y, x]
                print(f"({x},{y}): R={r} G={g} B={b} A={a}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        print("Shutting down...")
        browser.shutdown()

def test_pixel_streaming():
    """Test streaming raw pixels (simulate video capture)."""
    
    browser = simple_cef.SimpleCefBrowser(640, 480)
    
    try:
        if not browser.initialize():
            print("Failed to initialize CEF")
            return False
        
        browser.load_url("https://www.example.com")
        
        print("Starting pixel streaming simulation...")
        for frame in range(10):  # Capture 10 frames
            # Process CEF events
            for _ in range(5):
                browser.do_message_loop_work()
                time.sleep(0.01)
            
            # Get raw pixel buffer pointer (this would be passed to video encoder)
            pixels = browser.get_pixel_buffer()
            
            print(f"Frame {frame}: Buffer size = {browser.get_buffer_size()} bytes")
            print(f"  Dimensions: {browser.get_width()}x{browser.get_height()}")
            print(f"  Memory address: {pixels.data.hex()[:16]}...")
            
            time.sleep(0.1)  # Simulate processing delay
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        browser.shutdown()

if __name__ == "__main__":
    print("=== Simple CEF Browser Test ===")
    
    print("\n1. Testing basic browser functionality...")
    if test_simple_browser():
        print("✓ Basic test passed")
    else:
        print("✗ Basic test failed")
    
    print("\n2. Testing pixel streaming...")
    if test_pixel_streaming():
        print("✓ Streaming test passed")
    else:
        print("✗ Streaming test failed")
    
    print("\n=== Test Complete ===")