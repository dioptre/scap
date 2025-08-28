// Minimal CEF test that FORCES OnPaint to be called
#include "include/cef_app.h"
#include "include/cef_browser.h" 
#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include "include/wrapper/cef_library_loader.h"
#include <iostream>
#include <fstream>
#include <thread>
#include <chrono>

class ForceRenderHandler : public CefClient, public CefRenderHandler, public CefLifeSpanHandler {
public:
    ForceRenderHandler() {}
    
    CefRefPtr<CefRenderHandler> GetRenderHandler() override { return this; }
    CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
    
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override {
        rect.x = rect.y = 0;
        rect.width = 800;
        rect.height = 600;
        std::cout << "📐 GetViewRect called: 800x600" << std::endl;
    }
    
    void OnPaint(CefRefPtr<CefBrowser> browser, PaintElementType type,
                 const RectList& dirtyRects, const void* buffer,
                 int width, int height) override {
        std::cout << "🎉 ONPAINT CALLED! " << width << "x" << height << std::endl;
        
        if (buffer && width > 0 && height > 0) {
            // Save the image!
            std::ofstream file("RED_PAGE_PROOF.bgra", std::ios::binary);
            file.write(static_cast<const char*>(buffer), width * height * 4);
            file.close();
            
            // Count red pixels
            const unsigned char* pixels = static_cast<const unsigned char*>(buffer);
            int red_count = 0;
            
            for (int i = 0; i < width * height * 4; i += 4) {
                if (pixels[i+2] > 200 && pixels[i+1] < 100 && pixels[i] < 100) {
                    red_count++;
                }
            }
            
            std::cout << "🔴 RED PIXELS FOUND: " << red_count << std::endl;
            
            if (red_count > 1000) {
                std::cout << "✅ SUCCESS! RED PAGE RENDERED!" << std::endl;
            }
        }
    }
    
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override {
        browser_ = browser;
        std::cout << "✅ Browser created - will force rendering" << std::endl;
    }
    
    void OnBeforeClose(CefRefPtr<CefBrowser> browser) override {
        browser_ = nullptr;
    }
    
    CefRefPtr<CefBrowser> GetBrowser() { return browser_; }
    
private:
    CefRefPtr<CefBrowser> browser_;
    IMPLEMENT_REFCOUNTING(ForceRenderHandler);
};

int main(int argc, char* argv[]) {
    std::cout << "🧪 FORCING CEF OnPaint with Red Page" << std::endl;
    
    // Load CEF library
    CefScopedLibraryLoader library_loader;
    if (!library_loader.LoadInMain()) {
        return 1;
    }
    
    CefMainArgs main_args(argc, argv);
    
    // Handle subprocesses
    int exit_code = CefExecuteProcess(main_args, nullptr, nullptr);
    if (exit_code >= 0) return exit_code;
    
    // Settings
    CefSettings settings;
    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;
    settings.multi_threaded_message_loop = false;
    
    if (!CefInitialize(main_args, settings, nullptr, nullptr)) {
        return 1;
    }
    
    std::cout << "✅ CEF initialized - creating browser..." << std::endl;
    
    // Create handler  
    CefRefPtr<ForceRenderHandler> handler(new ForceRenderHandler());
    
    // Window info for headless
    CefWindowInfo window_info;
    window_info.SetAsWindowless(0);
    
    // Browser settings with higher frame rate
    CefBrowserSettings browser_settings;
    browser_settings.windowless_frame_rate = 30;
    
    // RED PAGE
    std::string url = "data:text/html,<html><body style='background:red;margin:0;'><h1 style='color:white;font-size:200px;text-align:center;'>RED!</h1></body></html>";
    
    // Create browser
    CefBrowserHost::CreateBrowser(window_info, handler, url, browser_settings, nullptr, nullptr);
    
    // AGGRESSIVE MESSAGE LOOP - FORCE ONPAINT
    std::cout << "🔄 Running aggressive message loop..." << std::endl;
    
    for (int i = 0; i < 200; ++i) {
        CefDoMessageLoopWork();
        
        // Force rendering every few iterations
        if (i > 20 && handler->GetBrowser()) {
            handler->GetBrowser()->GetHost()->Invalidate(PET_VIEW);
            handler->GetBrowser()->GetHost()->SendExternalBeginFrame();
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(25));
        
        if (i % 50 == 0) {
            std::cout << "  Iteration " << i << "..." << std::endl;
        }
    }
    
    std::cout << "✅ Message loop complete" << std::endl;
    
    CefShutdown();
    return 0;
}