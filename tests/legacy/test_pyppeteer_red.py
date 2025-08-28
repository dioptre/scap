#!/usr/bin/env python3
"""
Test pyppeteer (which uses Chromium headless) to render red page.
This should fucking work and give us the red page!
"""

import asyncio
from pyppeteer import launch
import os

async def test_red_page():
    print("🔥 Testing Pyppeteer Red Page Rendering")
    print("=" * 50)
    
    try:
        # Launch headless browser
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=900,600'
            ]
        })
        
        print("✅ Browser launched")
        
        # Create page
        page = await browser.newPage()
        await page.setViewport({'width': 900, 'height': 600})
        
        print("✅ Page created")
        
        # Navigate to red page
        red_html = '''
        <html>
        <body style="background-color: red; margin: 0; padding: 100px;">
            <h1 style="color: white; font-size: 100px; text-align: center;">
                RED PAGE TEST!
            </h1>
        </body>
        </html>
        '''
        
        await page.setContent(red_html)
        print("✅ Red HTML content set")
        
        # Wait for rendering
        await page.waitFor(2000)
        
        # Take screenshot
        screenshot_path = 'pyppeteer_red_page.png'
        await page.screenshot({'path': screenshot_path, 'fullPage': True})
        
        print(f"✅ Screenshot saved: {screenshot_path}")
        
        # Check if file exists and has content
        if os.path.exists(screenshot_path):
            size = os.path.getsize(screenshot_path)
            print(f"🎉 SUCCESS! Screenshot file: {size} bytes")
            
            # Also get page content to verify
            content = await page.content()
            if 'red' in content.lower():
                print("✅ Page content contains 'red'")
            
            return True
        else:
            print("❌ Screenshot file not created")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'browser' in locals():
            await browser.close()

async def main():
    print("🚀 SHOW ME THE FUCKING MONEY!")
    success = await test_red_page()
    
    if success:
        print("\n🎉 PYPPETEER WORKS!")
        print("We can now replace CEF with pyppeteer in your system!")
    else:
        print("\n❌ Even pyppeteer failed")

if __name__ == "__main__":
    asyncio.run(main())