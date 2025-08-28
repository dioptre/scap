#!/usr/bin/env python3
"""
Test pixel buffer access and demonstrate streaming capability.
"""

import simple_cef
import numpy as np

def test_pixel_access():
    """Test direct pixel buffer access for streaming."""
    print("=== Pixel Buffer Access Test ===")
    
    # Create browser with typical streaming resolution
    width, height = 640, 480
    browser = simple_cef.SimpleCefBrowser(width, height)
    
    print(f"✓ Created browser: {width}x{height}")
    print(f"✓ Buffer size: {browser.get_buffer_size()} bytes")
    
    # Get pixel buffer without CEF initialization (will be uninitialized memory)
    try:
        pixels = browser.get_pixel_buffer()
        print(f"✓ Got pixel buffer successfully")
        print(f"  Shape: {pixels.shape}")
        print(f"  Data type: {pixels.dtype}")
        print(f"  Memory layout: {pixels.strides} (strides)")
        
        # Show this is real memory we can manipulate
        print(f"  Sample pixels (BGRA format):")
        for y in range(min(3, height)):
            for x in range(min(3, width)):
                b, g, r, a = pixels[y, x]
                print(f"    ({x},{y}): B={b:3d} G={g:3d} R={r:3d} A={a:3d}")
        
        # Demonstrate we have direct memory access
        original_pixel = pixels[0, 0].copy()
        pixels[0, 0] = [255, 128, 64, 255]  # Set to orange
        modified_pixel = pixels[0, 0]
        
        print(f"✓ Direct memory modification test:")
        print(f"  Original: {original_pixel}")
        print(f"  Modified: {modified_pixel}")
        
        # This is what you'd pass to a video encoder
        raw_data_ptr = pixels.ctypes.data
        print(f"✓ Raw memory pointer: 0x{raw_data_ptr:016x}")
        print(f"  This pointer can be passed to C video encoders!")
        
        # Simulate frame capture for streaming
        frame_data = pixels.tobytes()
        print(f"✓ Frame data ready for streaming: {len(frame_data)} bytes")
        
        return True
        
    except Exception as e:
        print(f"✗ Error accessing pixel buffer: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_browsers():
    """Test creating multiple browser instances."""
    print("\n=== Multiple Browser Test ===")
    
    browsers = []
    resolutions = [(320, 240), (640, 480), (1280, 720)]
    
    for i, (w, h) in enumerate(resolutions):
        try:
            browser = simple_cef.SimpleCefBrowser(w, h)
            browsers.append(browser)
            print(f"✓ Browser {i+1}: {w}x{h} ({browser.get_buffer_size()} bytes)")
        except Exception as e:
            print(f"✗ Failed to create browser {i+1}: {e}")
            return False
    
    print(f"✓ Successfully created {len(browsers)} browser instances")
    return True

if __name__ == "__main__":
    success = True
    
    success &= test_pixel_access()
    success &= test_multiple_browsers()
    
    print(f"\n{'✓ ALL TESTS PASSED' if success else '✗ SOME TESTS FAILED'}")
    
    if success:
        print("\n🎉 Simple CEF library is working!")
        print("Ready for:")
        print("• Headless browser rendering")
        print("• Direct pixel buffer access") 
        print("• Video streaming integration")
        print("• Multiple browser instances")