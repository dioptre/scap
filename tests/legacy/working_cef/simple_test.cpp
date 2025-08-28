// Modified cefsimple to render red page and output JPG
#include "include/cef_app.h" 
#include "include/cef_browser.h"
#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include "include/wrapper/cef_library_loader.h"
#include "include/wrapper/cef_helpers.h"
#include <iostream>
#include <fstream>
#include <memory>
#include <thread>
#include <chrono>
#include <list>

class TestRenderHandler;

namespace {
    TestRenderHandler* g_instance = nullptr;
}

class TestRenderHandler : public CefClient,
                         public CefRenderHandler,
                         public CefLifeSpanHandler,
                         public CefLoadHandler {
public:
    TestRenderHandler() : pixel_buffer_(nullptr) {
        g_instance = this;
    }
    
    static TestRenderHandler* GetInstance() { return g_instance; }
    
    std::list<CefRefPtr<CefBrowser>> browser_list_;
    
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
        
        if (type == PET_VIEW) {
            // Save raw BGRA data
            std::ofstream file("test_output.bgra", std::ios::binary);
            file.write(static_cast<const char*>(buffer), width * height * 4);
            file.close();
            
            // Check for red pixels (simple test)
            const unsigned char* pixels = static_cast<const unsigned char*>(buffer);
            int red_pixels = 0;
            
            for (int i = 0; i < width * height * 4; i += 4) {
                unsigned char b = pixels[i];     // B
                unsigned char g = pixels[i+1];   // G  
                unsigned char r = pixels[i+2];   // R
                unsigned char a = pixels[i+3];   // A
                
                if (r > 200 && g < 100 && b < 100) {  // Red pixel
                    red_pixels++;
                }
            }
            
            std::cout << "🔴 Found " << red_pixels << " red pixels!" << std::endl;
            
            if (red_pixels > 1000) {
                std::cout << "✅ SUCCESS! Red page rendered successfully!" << std::endl;
            } else {
                std::cout << "⚠️ Not enough red pixels detected" << std::endl;
            }
        }
    }
    
    // CefLifeSpanHandler methods
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override {
        browser_ = browser;
        browser_list_.push_back(browser);
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
        
        // Force paint
        if (browser && browser->GetHost()) {
            browser->GetHost()->Invalidate(PET_VIEW);
        }
    }
    
private:
    CefRefPtr<CefBrowser> browser_;
    unsigned char* pixel_buffer_;
    
    IMPLEMENT_REFCOUNTING(TestRenderHandler);
};

class TestApp : public CefApp, public CefBrowserProcessHandler {
public:
    TestApp() {}
    
    CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override {
        return this;
    }
    
    void OnBeforeCommandLineProcessing(const CefString& process_type,
                                     CefRefPtr<CefCommandLine> command_line) override {
        // KEY FIX: Use --no-sandbox instead of --headless for OnPaint to work
        command_line->AppendSwitch("--no-sandbox");
        command_line->AppendSwitch("--disable-web-security");
        command_line->AppendSwitch("--enable-begin-frame-scheduling");
        // DO NOT USE --headless as it breaks OnPaint on macOS
        
        std::cout << "✅ Configured process for OnPaint: " << process_type.ToString() << std::endl;
    }
    
private:
    IMPLEMENT_REFCOUNTING(TestApp);
};

int main(int argc, char* argv[]) {
    std::cout << "🧪 Testing CEF Red Page Rendering" << std::endl;
    
    // Load the CEF framework library (CRITICAL for macOS)
    CefScopedLibraryLoader library_loader;
    if (!library_loader.LoadInMain()) {
        std::cerr << "❌ Failed to load CEF library" << std::endl;
        return 1;
    }
    std::cout << "✅ CEF library loaded" << std::endl;

    // Provide CEF with command-line arguments.
    CefMainArgs main_args(argc, argv);
    CefRefPtr<TestApp> app(new TestApp);

    // CEF applications have multiple sub-processes
    int exit_code = CefExecuteProcess(main_args, app, nullptr);
    if (exit_code >= 0) {
        std::cout << "Subprocess exit: " << exit_code << std::endl;
        return exit_code;
    }

    std::cout << "✅ Main process - initializing CEF..." << std::endl;

    // Specify CEF global settings here.
    CefSettings settings;
    settings.multi_threaded_message_loop = false;
    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;
    // settings.single_process = true;  // Not available in this version

    // Initialize CEF.
    if (!CefInitialize(main_args, settings, app.get(), nullptr)) {
        std::cerr << "❌ CefInitialize failed" << std::endl;
        return 1;
    }
    std::cout << "✅ CEF initialized!" << std::endl;

    // Create the handler
    CefRefPtr<TestRenderHandler> handler(new TestRenderHandler());
    
    // Information used when creating the native window.
    CefWindowInfo window_info;
    window_info.SetAsWindowless(0);  // Use 0 for this CEF version

    // Specify CEF browser settings here.
    CefBrowserSettings browser_settings;
    browser_settings.windowless_frame_rate = 10;

    // RED HTML PAGE TEST
    std::string red_html = "data:text/html,<html><body style='background-color:red;margin:0;padding:50px;'><h1 style='color:white;font-size:100px;text-align:center;'>RED PAGE TEST</h1></body></html>";

    // Create the browser
    std::cout << "🌐 Creating browser with red page..." << std::endl;
    CefBrowserHost::CreateBrowser(window_info, handler, red_html, browser_settings, nullptr, nullptr);

    // Run the message loop and FORCE frame scheduling
    std::cout << "🔄 Running message loop with frame scheduling..." << std::endl;
    
    // Wait for browser creation
    for (int i = 0; i < 50; ++i) {
        CefDoMessageLoopWork();
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    
    // Force frame rendering if browser was created
    auto handler_ptr = TestRenderHandler::GetInstance();
    if (handler_ptr && !handler_ptr->browser_list_.empty()) {
        auto browser = handler_ptr->browser_list_.front();
        std::cout << "🎬 Forcing frame render..." << std::endl;
        browser->GetHost()->SendExternalBeginFrame();
        browser->GetHost()->Invalidate(PET_VIEW);
        
        // Process more frames
        for (int i = 0; i < 100; ++i) {
            CefDoMessageLoopWork();
            browser->GetHost()->SendExternalBeginFrame();
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    }

    // Shut down
    CefShutdown();
    std::cout << "✅ Test complete - check for red pixels!" << std::endl;

    return 0;
}