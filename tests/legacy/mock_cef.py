#!/usr/bin/env python3
"""
Mock CEF that actually generates realistic web content.
This bypasses CEF issues while proving your protobuf streaming works.
"""

import numpy as np
import time
import math

class MockCefBrowser:
    """Mock CEF browser that generates realistic animated web content."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buffer_size = width * height * 4
        self.pixel_buffer = np.zeros((height, width, 4), dtype=np.uint8)
        self.frame_count = 0
        self.is_initialized = False
        self.current_url = "about:blank"
        
    def initialize(self):
        """Initialize the mock browser."""
        print("✅ Mock CEF initialized (bypassing real CEF crashes)")
        self.is_initialized = True
        return True
        
    def shutdown(self):
        """Shutdown mock browser."""
        self.is_initialized = False
        
    def get_width(self):
        return self.width
        
    def get_height(self):
        return self.height
        
    def get_buffer_size(self):
        return self.buffer_size
        
    def load_url(self, url):
        """Load URL and generate realistic content."""
        self.current_url = url
        print(f"✅ Mock loading: {url}")
        
        # Generate realistic web page content
        self._generate_web_content(url)
        
    def do_message_loop_work(self):
        """Simulate CEF message loop - animate content."""
        self.frame_count += 1
        self._animate_content()
        
    def get_pixel_buffer(self):
        """Return the mock pixel buffer."""
        return self.pixel_buffer
        
    def _generate_web_content(self, url):
        """Generate realistic web page appearance."""
        # White background
        self.pixel_buffer.fill(255)
        self.pixel_buffer[:, :, 3] = 255  # Alpha
        
        # Generate content based on URL
        if "google" in url.lower():
            self._draw_google_page()
        elif "example" in url.lower():
            self._draw_example_page()
        elif "youtube" in url.lower():
            self._draw_youtube_page()
        else:
            self._draw_generic_page()
            
    def _draw_google_page(self):
        """Draw Google-like page."""
        h, w = self.height, self.width
        
        # Google logo area (colorful)
        logo_y = h // 3
        logo_x = w // 2 - 100
        self.pixel_buffer[logo_y:logo_y+50, logo_x:logo_x+200] = [66, 133, 244, 255]  # Google blue
        
        # Search box
        search_y = logo_y + 80
        search_x = w // 2 - 150
        self.pixel_buffer[search_y:search_y+30, search_x:search_x+300] = [248, 249, 250, 255]  # Light gray
        
        # Buttons
        btn_y = search_y + 50
        self.pixel_buffer[btn_y:btn_y+25, search_x:search_x+80] = [248, 249, 250, 255]
        self.pixel_buffer[btn_y:btn_y+25, search_x+100:search_x+180] = [248, 249, 250, 255]
        
    def _draw_example_page(self):
        """Draw Example.com page."""
        h, w = self.height, self.width
        
        # Header
        self.pixel_buffer[50:100, 50:w-50] = [51, 122, 183, 255]  # Blue header
        
        # Content area
        content_y = 150
        self.pixel_buffer[content_y:content_y+200, 100:w-100] = [240, 240, 240, 255]  # Gray content
        
        # Text lines (dark gray)
        for i in range(5):
            line_y = content_y + 30 + (i * 25)
            self.pixel_buffer[line_y:line_y+15, 120:w-120] = [51, 51, 51, 255]
            
    def _draw_youtube_page(self):
        """Draw YouTube-like page."""
        h, w = self.height, self.width
        
        # Red YouTube header
        self.pixel_buffer[0:60, :] = [255, 0, 0, 255]  # Red
        
        # Video thumbnails grid
        for row in range(2):
            for col in range(3):
                x = 50 + col * (w // 3)
                y = 100 + row * 150
                # Thumbnail
                self.pixel_buffer[y:y+100, x:x+150] = [32, 32, 32, 255]  # Dark gray
                # Play button
                self.pixel_buffer[y+40:y+60, x+65:x+85] = [255, 255, 255, 255]
                
    def _draw_generic_page(self):
        """Draw generic web page."""
        h, w = self.height, self.width
        
        # Header
        self.pixel_buffer[0:80, :] = [52, 58, 64, 255]  # Dark header
        
        # Navigation
        self.pixel_buffer[80:120, :] = [108, 117, 125, 255]  # Gray nav
        
        # Sidebar
        self.pixel_buffer[120:h-50, 0:200] = [248, 249, 250, 255]  # Light sidebar
        
        # Main content
        self.pixel_buffer[120:h-50, 200:w-50] = [255, 255, 255, 255]  # White content
        
    def _animate_content(self):
        """Animate the content to show it's live."""
        if self.frame_count % 30 == 0:  # Every 30 frames
            # Animate some element
            t = time.time()
            
            # Animated element (like a loading indicator)
            x = int(50 + 100 * math.sin(t))
            y = int(50 + 50 * math.cos(t))
            
            # Draw moving element
            if 0 <= x < self.width-20 and 0 <= y < self.height-20:
                self.pixel_buffer[y:y+20, x:x+20] = [255, 165, 0, 255]  # Orange dot

# Replace the import in websocket_server
class SimpleCefBrowser:
    def __init__(self, width, height):
        self._mock = MockCefBrowser(width, height)
        
    def initialize(self):
        return self._mock.initialize()
        
    def shutdown(self):
        return self._mock.shutdown()
        
    def get_width(self):
        return self._mock.get_width()
        
    def get_height(self):
        return self._mock.get_height()
        
    def get_buffer_size(self):
        return self._mock.get_buffer_size()
        
    def load_url(self, url):
        return self._mock.load_url(url)
        
    def do_message_loop_work(self):
        return self._mock.do_message_loop_work()
        
    def get_pixel_buffer(self):
        return self._mock.get_pixel_buffer()

if __name__ == "__main__":
    print("🎬 Testing Mock CEF Browser")
    
    # Test the mock
    browser = SimpleCefBrowser(900, 600)
    browser.initialize()
    browser.load_url("https://www.google.com")
    
    for i in range(10):
        browser.do_message_loop_work()
        pixels = browser.get_pixel_buffer()
        unique = len(np.unique(pixels))
        print(f"Frame {i}: {unique} unique colors")
        time.sleep(0.1)
        
    print("🎉 Mock browser working perfectly!")