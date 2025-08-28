#include "include/cef_app.h"
#include "include/cef_browser.h"
#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include <iostream>
#include <fstream>
#include <thread>
#include <chrono>

class MinimalHandler : public CefClient,
                       public CefRenderHandler,
                       public CefLifeSpanHandler,
                       public CefLoadHandler {
public:
    MinimalHandler() : pixel_buffer_(nullptr) {}
    
    // CefClient methods
    CefRefPtr<CefRenderHandler> GetRenderHandler() override { return this; }
    CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
    CefRefPtr<CefLoadHandler> GetLoadHandler() override { return this; }
    
    // CefRenderHandler methods
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override {
        rect.x = rect.y = 0;
        rect.width = 800;
        rect.height = 600;
    }
    
    void OnPaint(CefRefPtr<CefBrowser> browser,
                 PaintElementType type,
                 const RectList& dirtyRects,
                 const void* buffer,
                 int width,
                 int height) override {
        
        std::cout << "🎉 OnPaint called! " << width << "x" << height << std::endl;
        
        // Save the frame to prove it's working
        if (type == PET_VIEW) {
            std::ofstream file("cef_frame_proof.rgba", std::ios::binary);
            file.write(static_cast<const char*>(buffer), width * height * 4);
            file.close();
            std::cout << "✅ Frame saved to cef_frame_proof.rgba" << std::endl;
        }
    }
    
    // CefLifeSpanHandler methods
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override {
        browser_ = browser;
        std::cout << "✅ Browser created" << std::endl;
    }
    
    void OnBeforeClose(CefRefPtr<CefBrowser> browser) override {
        browser_ = nullptr;
    }
    
    // CefLoadHandler methods
    void OnLoadEnd(CefRefPtr<CefBrowser> browser,
                   CefRefPtr<CefFrame> frame,
                   int httpStatusCode) override {
        std::cout << "✅ Page loaded: " << httpStatusCode << std::endl;
        
        // Force paint after load
        if (browser && browser->GetHost()) {
            browser->GetHost()->Invalidate(PET_VIEW);
        }
    }
    
private:
    CefRefPtr<CefBrowser> browser_;
    unsigned char* pixel_buffer_;
    
    IMPLEMENT_REFCOUNTING(MinimalHandler);
};

class MinimalApp : public CefApp, public CefBrowserProcessHandler {
public:
    MinimalApp() {}
    
    CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override {
        return this;
    }
    
    void OnBeforeCommandLineProcessing(const CefString& process_type,
                                     CefRefPtr<CefCommandLine> command_line) override {
        // Minimal flags for headless rendering
        command_line->AppendSwitch("--no-sandbox");
        std::cout << "✅ Added minimal CEF flags" << std::endl;
    }
    
private:
    IMPLEMENT_REFCOUNTING(MinimalApp);
};

int main(int argc, char* argv[]) {
    std::cout << "🧪 Testing Minimal CEF Headless Browser" << std::endl;
    
    // CEF settings
    CefSettings settings;
    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;
    settings.log_severity = LOGSEVERITY_INFO;
    settings.multi_threaded_message_loop = false;
    
    // Initialize CEF
    CefMainArgs main_args(argc, argv);
    CefRefPtr<CefApp> app(new MinimalApp());
    
    if (!CefInitialize(main_args, settings, app.get(), nullptr)) {
        std::cerr << "❌ CEF initialization failed" << std::endl;
        return 1;
    }
    
    std::cout << "✅ CEF initialized successfully" << std::endl;
    
    // Create handler
    CefRefPtr<MinimalHandler> handler(new MinimalHandler());
    
    // Window info for headless
    CefWindowInfo window_info;
    window_info.SetAsWindowless(0);
    
    // Browser settings
    CefBrowserSettings browser_settings;
    browser_settings.windowless_frame_rate = 10;
    
    // Create browser
    std::cout << "🌐 Creating browser..." << std::endl;
    CefBrowserHost::CreateBrowser(window_info, handler, "data:text/html,<h1 style='color:red;font-size:100px;'>WORKING!</h1>", browser_settings, nullptr, nullptr);
    
    // Run message loop
    std::cout << "🔄 Running message loop..." << std::endl;
    for (int i = 0; i < 200; ++i) {
        CefDoMessageLoopWork();
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    
    std::cout << "🛑 Shutting down CEF" << std::endl;
    CefShutdown();
    
    return 0;
}