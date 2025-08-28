#!/usr/bin/env python3
"""
Test pixel buffer access without full CEF initialization.
"""

import simple_cef
import numpy as np

def test_pixel_buffer():
    """Test pixel buffer access."""
    print("=== Pixel Buffer Test ===")
    
    browser = simple_cef.SimpleCefBrowser(640, 480)
    print(f"✓ Browser created: {browser.get_width()}x{browser.get_height()}")
    
    # Get pixel buffer (will be uninitialized/black)
    pixels = browser.get_pixel_buffer()
    print(f"✓ Pixel buffer retrieved")
    print(f"  Shape: {pixels.shape}")
    print(f"  Data type: {pixels.dtype}")
    print(f"  Size: {pixels.nbytes} bytes")
    
    # Check that we can access pixel data
    print(f"  Sample pixel at (0,0): BGRA = {pixels[0, 0]}")
    print(f"  Buffer memory address: 0x{pixels.data.hex()[:16]}...")
    
    # This demonstrates the raw pixel access that can be used for streaming
    print(f"✓ Raw pixel buffer is accessible for streaming!")
    
    return True

if __name__ == "__main__":
    test_pixel_buffer()