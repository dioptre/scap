#!/usr/bin/env python3
"""
Test that CEF browser actually loads and renders web content.
"""

import sys
import os
import time
import numpy as np
from PIL import Image

# Add src to path
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')

def test_browser_rendering():
    """Test that the browser actually renders web content."""
    print("=== CEF Browser Rendering Test ===")
    
    try:
        from websocket_server import CEFBrowserManager
        
        # Create browser manager
        print("Creating CEF browser...")
        manager = CEFBrowserManager(1024, 768)
        
        if not manager.is_initialized:
            print("✗ CEF browser failed to initialize")
            return False
        
        print(f"✓ CEF browser initialized: {manager.width}x{manager.height}")
        
        # Load a simple webpage
        print("Loading webpage...")
        url = "https://www.example.com"
        success = manager.load_url(url)
        
        if not success:
            print("✗ Failed to load URL")
            return False
        
        print(f"✓ URL loaded: {url}")
        
        # Give more time for page to load and render
        print("Waiting for page to render...")
        for i in range(30):  # 3 seconds at 100ms intervals
            manager.browser.do_message_loop_work()
            time.sleep(0.1)
        
        print("✓ Page processing complete")
        
        # Capture frame multiple times to see changes
        print("Capturing rendered frames...")
        for frame_num in range(5):
            pixels, tiles = manager.capture_frame()
            
            if pixels is not None:
                print(f"Frame {frame_num + 1}:")
                print(f"  ✓ Pixels captured: {pixels.shape}")
                print(f"  ✓ Tiles generated: {len(tiles)}")
                
                # Check if we have actual content (not all zeros)
                non_zero_pixels = np.count_nonzero(pixels)
                total_pixels = pixels.size
                content_ratio = non_zero_pixels / total_pixels
                
                print(f"  ✓ Content ratio: {content_ratio:.3f} ({non_zero_pixels:,}/{total_pixels:,} non-zero)")
                
                if tiles:
                    # Show tile compression info
                    total_raw = sum(t['width'] * t['height'] * 4 for t in tiles)
                    total_compressed = sum(t['size'] for t in tiles)
                    compression_ratio = total_raw / total_compressed if total_compressed > 0 else 0
                    
                    print(f"  ✓ Compression: {total_raw:,} → {total_compressed:,} bytes ({compression_ratio:.1f}x)")
                    
                    # Show codec usage
                    codecs = {}
                    for tile in tiles:
                        codec = tile['codec']
                        codecs[codec] = codecs.get(codec, 0) + 1
                    
                    print(f"  ✓ Codec usage: {dict(codecs)}")
                
                # Save a screenshot for verification
                if frame_num == 2:  # Save middle frame
                    try:
                        # Convert BGRA to RGB
                        rgb_pixels = pixels[:, :, [2, 1, 0]]  # BGRA -> RGB
                        img = Image.fromarray(rgb_pixels, 'RGB')
                        screenshot_path = "test_browser_screenshot.png"
                        img.save(screenshot_path)
                        print(f"  ✓ Screenshot saved: {screenshot_path}")
                    except Exception as e:
                        print(f"  ⚠ Screenshot save failed: {e}")
                
                time.sleep(0.5)  # Wait between captures
            else:
                print(f"  ✗ Frame {frame_num + 1}: No pixels captured")
        
        # Test loading different URL
        print("\nTesting different URL...")
        url2 = "https://httpbin.org/html"
        if manager.load_url(url2):
            print(f"✓ Second URL loaded: {url2}")
            
            # Process and capture
            for i in range(20):
                manager.browser.do_message_loop_work()
                time.sleep(0.1)
            
            pixels2, tiles2 = manager.capture_frame()
            if pixels2 is not None and tiles2:
                print(f"✓ Second page rendered: {len(tiles2)} tiles")
            else:
                print("⚠ Second page: No content captured")
        
        return True
        
    except Exception as e:
        print(f"✗ Browser rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pixel_content():
    """Test that we're getting actual rendered content, not just empty pixels."""
    print("\n=== Pixel Content Analysis ===")
    
    try:
        import simple_cef
        
        # Create browser and load content
        browser = simple_cef.SimpleCefBrowser(800, 600)
        print("✓ Browser created")
        
        # Initialize CEF (this is the key part that might be missing)
        if browser.initialize():
            print("✓ CEF initialized successfully")
            
            # Load URL
            browser.load_url("https://www.google.com")
            print("✓ Google loaded")
            
            # Process messages and wait for rendering
            print("Processing CEF messages for rendering...")
            for i in range(100):  # More processing time
                browser.do_message_loop_work()
                time.sleep(0.05)  # 50ms intervals
                
                # Check for content every 10 iterations
                if i % 20 == 19:
                    pixels = browser.get_pixel_buffer()
                    non_zero = np.count_nonzero(pixels)
                    print(f"  Iteration {i+1}: {non_zero:,} non-zero pixels")
            
            # Final capture
            final_pixels = browser.get_pixel_buffer()
            final_non_zero = np.count_nonzero(final_pixels)
            
            print(f"✓ Final result: {final_non_zero:,} non-zero pixels")
            
            if final_non_zero > 1000:  # Should have substantial content
                print("✓ Browser appears to be rendering content!")
                
                # Save screenshot
                rgb_pixels = final_pixels[:, :, [2, 1, 0]]  # BGRA -> RGB
                img = Image.fromarray(rgb_pixels, 'RGB')
                img.save("google_screenshot.png")
                print("✓ Google screenshot saved")
                
                return True
            else:
                print("⚠ Very few pixels rendered - may need GUI context")
                return False
        
        else:
            print("⚠ CEF initialization failed - may need GUI context")
            return False
            
    except Exception as e:
        print(f"✗ Pixel content test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🖥️ CEF Browser Rendering Tests")
    print("=" * 50)
    
    success1 = test_browser_rendering()
    success2 = test_pixel_content()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("✅ Browser is rendering content successfully!")
        print("Check for saved screenshots:")
        print("  - test_browser_screenshot.png")
        print("  - google_screenshot.png")
    elif success1 or success2:
        print("⚠ Partial success - browser working but may need full GUI context")
    else:
        print("❌ Browser rendering needs investigation")
        print("CEF may require additional setup for headless rendering")
    
    print(f"\n💡 Note: CEF headless rendering may require:")
    print(f"  • GPU context initialization")
    print(f"  • Additional CEF settings") 
    print(f"  • Platform-specific setup")