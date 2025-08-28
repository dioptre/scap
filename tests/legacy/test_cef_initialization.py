#!/usr/bin/env python3
"""
Test CEF browser initialization and basic rendering.
"""

import simple_cef
import numpy as np
import time

def test_cef_initialization():
    """Test proper CEF initialization."""
    print("=== CEF Initialization Test ===")
    
    try:
        # Create browser
        browser = simple_cef.SimpleCefBrowser(640, 480)
        print(f"✓ Browser created: {browser.get_width()}x{browser.get_height()}")
        
        # Initialize CEF properly
        print("Initializing CEF...")
        if browser.initialize():
            print("✓ CEF initialized successfully!")
            
            # Load a URL
            print("Loading URL...")
            browser.load_url("https://www.example.com")
            print("✓ URL load requested")
            
            # Process CEF messages and wait
            print("Processing CEF messages for rendering...")
            for i in range(100):
                browser.do_message_loop_work()
                time.sleep(0.05)
                
                # Check for content every 20 iterations
                if i % 20 == 19:
                    pixels = browser.get_pixel_buffer()
                    non_zero = np.count_nonzero(pixels)
                    print(f"  Iteration {i+1}: {non_zero:,} non-zero pixels")
                    
                    if non_zero > 1000:
                        print("  ✓ Content detected!")
                        break
            
            # Final check
            final_pixels = browser.get_pixel_buffer()
            final_non_zero = np.count_nonzero(final_pixels)
            print(f"✓ Final result: {final_non_zero:,} non-zero pixels")
            
            if final_non_zero > 1000:
                print("🎉 SUCCESS: Browser is rendering content!")
                
                # Save screenshot
                from PIL import Image
                rgb_pixels = final_pixels[:, :, [2, 1, 0]]  # BGRA -> RGB
                img = Image.fromarray(rgb_pixels)
                img.save("cef_test_screenshot.png")
                print("✓ Screenshot saved: cef_test_screenshot.png")
                
                return True
            else:
                print("⚠ Limited rendering - may need additional setup")
                return False
                
        else:
            print("✗ CEF initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            browser.shutdown()
            print("✓ Browser shutdown complete")
        except:
            pass

def test_websocket_with_rendering():
    """Test the websocket server with actual rendering."""
    print("\n=== WebSocket Server with Rendering Test ===")
    
    try:
        import sys
        import os
        sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')
        
        from websocket_server import CEFBrowserManager
        
        # Create browser manager
        manager = CEFBrowserManager(800, 600)
        print(f"✓ Browser manager created: {manager.width}x{manager.height}")
        
        if manager.is_initialized:
            print("✓ CEF initialized in manager")
            
            # Load URL
            url = "https://httpbin.org/html"
            if manager.load_url(url):
                print(f"✓ URL loaded: {url}")
                
                # Capture frames
                for frame_num in range(10):
                    pixels, tiles = manager.capture_frame()
                    
                    if pixels is not None and len(tiles) > 0:
                        non_zero = np.count_nonzero(pixels)
                        total_size = sum(t['size'] for t in tiles)
                        codecs = set(t['codec'] for t in tiles)
                        
                        print(f"  Frame {frame_num+1}: {non_zero:,} pixels, {len(tiles)} tiles, {total_size} bytes, codecs: {codecs}")
                        
                        if non_zero > 5000:  # Substantial content
                            print("  🎉 Frame has substantial content!")
                            return True
                    
                    time.sleep(0.5)
                
                print("⚠ Frames captured but limited content")
                return False
            else:
                print("✗ URL loading failed")
                return False
        else:
            print("✗ CEF not initialized in manager")
            return False
            
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 CEF Browser Rendering Verification")
    print("=" * 50)
    
    # Test basic CEF initialization
    test1_success = test_cef_initialization()
    
    # Test websocket server integration
    test2_success = test_websocket_with_rendering()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"  CEF Initialization: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  WebSocket Integration: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The browser is successfully rendering web content!")
        print("Check cef_test_screenshot.png for visual confirmation.")
    elif test1_success or test2_success:
        print("\n⚠ PARTIAL SUCCESS")
        print("Basic functionality works, full rendering may need GUI context.")
    else:
        print("\n🔍 NEEDS INVESTIGATION")
        print("CEF may require additional platform-specific setup.")
        print("Try running on a system with display/GPU access.")