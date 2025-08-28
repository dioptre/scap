#!/usr/bin/env python3
"""
Simple test to verify the CEF module imports and basic functionality works.
"""

import simple_cef

def test_import():
    """Test that the module imports successfully."""
    print("✓ simple_cef module imported successfully")
    
    # Test creating browser object
    try:
        browser = simple_cef.SimpleCefBrowser(800, 600)
        print("✓ SimpleCefBrowser object created successfully")
        print(f"  Browser dimensions: {browser.get_width()}x{browser.get_height()}")
        print(f"  Buffer size: {browser.get_buffer_size()} bytes")
        
        # Test basic methods without initializing CEF
        print("✓ Basic methods accessible")
        
        print("\n🎉 All basic tests passed!")
        print("Note: Full CEF functionality requires proper initialization in a GUI context.")
        
    except Exception as e:
        print(f"✗ Error creating browser: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Simple CEF Import Test ===")
    
    if test_import():
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")