#!/usr/bin/env python3
"""
Debug what CEF is actually capturing.
"""

import sys
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')
import simple_cef
import numpy as np
import time
from PIL import Image

def debug_cef_rendering():
    print("🔍 Debugging CEF Rendering")
    print("=" * 30)
    
    # Create browser
    browser = simple_cef.SimpleCefBrowser(640, 480)
    print(f"✓ Browser created: {browser.get_width()}x{browser.get_height()}")
    
    # Check initial pixel buffer
    initial_pixels = browser.get_pixel_buffer()
    initial_unique = len(np.unique(initial_pixels))
    print(f"✓ Initial pixel buffer: {initial_unique} unique values")
    
    # Try initialization
    print("🔧 Initializing CEF...")
    if browser.initialize():
        print("✓ CEF initialized successfully")
        
        # Load a simple URL
        print("🌐 Loading test URL...")
        browser.load_url("data:text/html,<html><body style='background:red;color:white;font-size:48px;'>TEST PAGE</body></html>")
        
        # Process message loop extensively
        print("⏳ Processing message loop...")
        for i in range(200):
            browser.do_message_loop_work()
            time.sleep(0.05)
            
            if i % 50 == 49:
                pixels = browser.get_pixel_buffer()
                unique_vals = len(np.unique(pixels))
                non_zero = np.count_nonzero(pixels)
                print(f"  Step {i+1}: {unique_vals} unique values, {non_zero:,} non-zero pixels")
                
                # Save snapshot
                rgb_pixels = pixels[:, :, [2, 1, 0]]
                img = Image.fromarray(rgb_pixels)
                img.save(f"debug_step_{i+1}.png")
                
                if unique_vals > 10:  # More than just white
                    print("  🎉 Content detected!")
                    break
        
        # Final check
        final_pixels = browser.get_pixel_buffer()
        final_unique = len(np.unique(final_pixels))
        final_non_zero = np.count_nonzero(final_pixels)
        
        print(f"\n📊 Final result:")
        print(f"  Unique values: {final_unique}")
        print(f"  Non-zero pixels: {final_non_zero:,}")
        
        if final_unique > 10:
            print("✅ CEF is rendering content!")
        else:
            print("⚠️ CEF is only showing background")
        
        # Save final image
        rgb_pixels = final_pixels[:, :, [2, 1, 0]]
        img = Image.fromarray(rgb_pixels)
        img.save("debug_final.png")
        print("💾 Saved debug_final.png")
        
        browser.shutdown()
        return final_unique > 10
        
    else:
        print("✗ CEF initialization failed")
        return False

if __name__ == "__main__":
    debug_cef_rendering()