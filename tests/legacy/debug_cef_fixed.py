#!/usr/bin/env python3
"""
Debug CEF with BLAS threading fix for macOS.
"""

import os
# CRITICAL: Set these BEFORE importing numpy to prevent BLAS threading
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

print("🔧 Set single-threaded BLAS before numpy import")

import sys
sys.path.insert(0, '/Users/andrewgrosser/Documents/scap/src')
import simple_cef
import numpy as np
import time
from PIL import Image

def debug_cef_rendering():
    print("🔍 Debugging CEF Rendering (BLAS threading fixed)")
    print("=" * 50)
    
    # Create browser
    browser = simple_cef.SimpleCefBrowser(640, 480)
    print(f"✓ Browser created: {browser.get_width()}x{browser.get_height()}")
    
    # Try initialization
    print("🔧 Initializing CEF (should not crash now)...")
    try:
        if browser.initialize():
            print("🎉 CEF initialized successfully!")
            
            # Load a simple URL  
            print("🌐 Loading test URL...")
            browser.load_url("data:text/html,<html><body style='background:red;color:white;font-size:48px;text-align:center;padding:100px;'>WORKING!</body></html>")
            
            # Process message loop extensively
            print("⏳ Processing message loop...")
            for i in range(100):
                browser.do_message_loop_work()
                time.sleep(0.1)
                
                if i % 20 == 19:
                    pixels = browser.get_pixel_buffer()
                    unique_vals = len(np.unique(pixels))
                    non_zero = np.count_nonzero(pixels)
                    print(f"  Step {i+1}: {unique_vals} unique values, {non_zero:,} non-zero pixels")
                    
                    if unique_vals > 20:  # More variation than just white
                        print("  🎉 Content detected!")
                        break
            
            # Final check
            final_pixels = browser.get_pixel_buffer()
            final_unique = len(np.unique(final_pixels))
            final_non_zero = np.count_nonzero(final_pixels)
            
            print(f"\n📊 Final result:")
            print(f"  Unique values: {final_unique}")
            print(f"  Non-zero pixels: {final_non_zero:,}")
            
            if final_unique > 20:
                print("🎉 CEF is rendering actual content!")
            else:
                print("⚠️ CEF is showing background only")
            
            # Save final image
            rgb_pixels = final_pixels[:, :, [2, 1, 0]]
            img = Image.fromarray(rgb_pixels)
            img.save("debug_cef_working.png")
            print("💾 Saved debug_cef_working.png")
            
            browser.shutdown()
            return final_unique > 20
            
        else:
            print("✗ CEF initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_cef_rendering()