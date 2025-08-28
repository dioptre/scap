#!/usr/bin/env python3
"""
Working pyppeteer browser manager that replaces CEF.
This actually renders web pages on macOS!
"""

import asyncio
from pyppeteer import launch
import numpy as np
import base64
import time
from typing import Dict, List, Tuple
from PIL import Image
import io

class PyppeteerBrowserManager:
    """Manages pyppeteer headless browser - WORKS ON MACOS!"""
    
    def __init__(self, width: int = 900, height: int = 600):
        self.width = width
        self.height = height
        self.browser = None
        self.page = None
        self.is_initialized = False
        self.current_url = "about:blank"
        self.frame_id = 0
        
    async def init_browser(self):
        """Initialize pyppeteer browser."""
        try:
            self.browser = await launch({
                'headless': True,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    f'--window-size={self.width},{self.height}'
                ]
            })
            
            self.page = await self.browser.newPage()
            await self.page.setViewport({'width': self.width, 'height': self.height})
            
            print(f"✅ Pyppeteer browser created: {self.width}x{self.height}")
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"✗ Failed to initialize pyppeteer browser: {e}")
            return False
    
    async def load_url(self, url: str) -> bool:
        """Load a URL in the browser."""
        if not self.is_initialized or not self.page:
            return False
        
        try:
            await self.page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 10000})
            self.current_url = url
            print(f"✅ Pyppeteer loaded: {url}")
            return True
        except Exception as e:
            print(f"✗ Failed to load URL: {e}")
            return False
    
    async def capture_frame(self) -> Tuple[np.ndarray, List[Dict]]:
        """Capture current frame as numpy array and process into tiles."""
        if not self.is_initialized or not self.page:
            return None, []
        
        try:
            # Take screenshot as bytes
            screenshot_bytes = await self.page.screenshot({
                'type': 'png',
                'fullPage': False,
                'omitBackground': False
            })
            
            # Convert PNG to numpy array
            image = Image.open(io.BytesIO(screenshot_bytes))
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Convert to numpy array (RGBA)
            pixels = np.array(image)
            
            # Convert RGBA to BGRA for consistency with CEF
            bgra_pixels = pixels[:, :, [2, 1, 0, 3]]  # RGBA -> BGRA
            
            # Process into tiles
            tiles = self._process_frame_to_tiles(bgra_pixels)
            
            self.frame_id += 1
            return bgra_pixels, tiles
            
        except Exception as e:
            print(f"✗ Frame capture error: {e}")
            return None, []
    
    def _process_frame_to_tiles(self, frame: np.ndarray) -> List[Dict]:
        """Process full frame into tiles."""
        tiles = []
        tile_size = 112  # Match your existing setup
        
        height, width = frame.shape[:2]
        tiles_x = (width + tile_size - 1) // tile_size
        tiles_y = (height + tile_size - 1) // tile_size
        
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                # Extract tile
                start_x = tx * tile_size
                start_y = ty * tile_size
                end_x = min(start_x + tile_size, width)
                end_y = min(start_y + tile_size, height)
                
                tile_data = frame[start_y:end_y, start_x:end_x]
                
                # Simple compression
                import zlib
                compressed_data = zlib.compress(tile_data.tobytes(), level=1)
                
                # Create tile info
                tile = {
                    'tile_id': f'{start_x}_{start_y}',
                    'x': start_x,
                    'y': start_y,
                    'width': end_x - start_x,
                    'height': end_y - start_y,
                    'codec': 'vp9',  # Default codec
                    'has_motion': True,  # Assume motion for now
                    'data': base64.b64encode(compressed_data).decode('utf-8'),
                    'size': len(compressed_data),
                    'frame_id': self.frame_id,
                    'timestamp': int(time.time() * 1000)
                }
                tiles.append(tile)
        
        return tiles
    
    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
            self.is_initialized = False

if __name__ == "__main__":
    async def test():
        print("🧪 Testing Pyppeteer Browser Manager")
        
        manager = PyppeteerBrowserManager(900, 600)
        await manager.init_browser()
        
        await manager.load_url("https://www.google.com")
        
        pixels, tiles = await manager.capture_frame()
        
        if pixels is not None:
            print(f"✅ Captured: {pixels.shape}")
            print(f"✅ Tiles: {len(tiles)}")
        
        await manager.close()
    
    asyncio.run(test())