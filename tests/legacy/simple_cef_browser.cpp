#include "simple_cef_browser.h"
#include "include/cef_sandbox_mac.h"
#include "include/wrapper/cef_library_loader.h"
#include <iostream>
#include <thread>
#include <chrono>

SimpleCefBrowser::SimpleCefBrowser(int width, int height) 
    : width_(width), height_(height), is_initialized_(false) {
    buffer_size_ = width * height * 4; // BGRA format
    pixel_buffer_ = std::make_unique<unsigned char[]>(buffer_size_);
    
    // Initialize with white background to show something is happening
    for (size_t i = 0; i < buffer_size_; i += 4) {
        pixel_buffer_[i] = 255;     // B
        pixel_buffer_[i+1] = 255;   // G
        pixel_buffer_[i+2] = 255;   // R
        pixel_buffer_[i+3] = 255;   // A
    }
}

SimpleCefBrowser::~SimpleCefBrowser() {
    if (is_initialized_) {
        Shutdown();
    }
}

bool SimpleCefBrowser::Initialize() {
    if (is_initialized_) {
        return true;
    }

    // CRITICAL: Use CefScopedLibraryLoader (the key to working CEF on macOS)
    static CefScopedLibraryLoader library_loader;
    if (!library_loader.LoadInMain()) {
        std::cerr << "Failed to load CEF library" << std::endl;
        return false;
    }
    std::cout << "✅ CEF library loaded successfully" << std::endl;

    // Handle subprocess execution
    CefMainArgs main_args;
    CefRefPtr<CefApp> app(new SimpleCefApp());
    
    // Check if this is a subprocess
    int exit_code = CefExecuteProcess(main_args, app.get(), nullptr);
    if (exit_code >= 0) {
        std::cout << "Subprocess exit: " << exit_code << std::endl;
        exit(exit_code);
    }
    
    std::cout << "Main process - initializing CEF..." << std::endl;

    // CEF settings - disable ALL optional components
    CefSettings settings;
    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;
    settings.log_severity = LOGSEVERITY_DISABLE;  // Disable all logging
    
    // Essential macOS settings
    settings.multi_threaded_message_loop = false;
    settings.command_line_args_disabled = false;
    
    // DISABLE ALL OPTIONAL COMPONENTS
    settings.pack_loading_disabled = true;       // Disable pak files
    settings.resources_dir_path.str = nullptr;   // No resources
    settings.locales_dir_path.str = nullptr;     // No locales  
    CefString(&settings.user_agent).FromString("HeadlessBot/1.0");
    
    if (!CefInitialize(main_args, settings, app.get(), nullptr)) {
        std::cerr << "Failed to initialize CEF" << std::endl;
        return false;
    }

    // Create browser window info for headless
    CefWindowInfo window_info;
    window_info.SetAsWindowless(0); // 0 = no parent window for headless
    
    // Set bounds for rendering
    CefRect rect;
    rect.x = 0;
    rect.y = 0; 
    rect.width = width_;
    rect.height = height_;
    
    // Browser settings
    CefBrowserSettings browser_settings;
    browser_settings.windowless_frame_rate = 30; // 30 FPS
    browser_settings.background_color = CefColorSetARGB(255, 255, 255, 255); // White background
    
    // Enable browser features
    CefString(&browser_settings.default_encoding).FromString("utf-8");
    browser_settings.javascript = STATE_ENABLED;

    // Create browser - this is async!
    if (!CefBrowserHost::CreateBrowser(window_info, this, "about:blank", browser_settings, nullptr, nullptr)) {
        std::cerr << "Failed to create CEF browser" << std::endl;
        CefShutdown();
        return false;
    }
    
    // Wait for browser to be created (with timeout)
    int timeout = 50; // 5 seconds
    while (!browser_ && timeout > 0) {
        CefDoMessageLoopWork();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        timeout--;
    }
    
    if (!browser_) {
        std::cerr << "Browser creation timed out" << std::endl;
        CefShutdown();
        return false;
    }
    
    is_initialized_ = true;
    return true;
}

void SimpleCefBrowser::Shutdown() {
    if (!is_initialized_) {
        return;
    }
    
    if (browser_) {
        browser_->GetHost()->CloseBrowser(true);
        browser_ = nullptr;
    }
    
    CefShutdown();
    is_initialized_ = false;
}

void SimpleCefBrowser::LoadURL(const std::string& url) {
    if (browser_) {
        std::cout << "Loading URL: " << url << std::endl;
        browser_->GetMainFrame()->LoadURL(url);
        
        // Process message loop to handle the load
        for (int i = 0; i < 100; ++i) {
            CefDoMessageLoopWork();
            std::this_thread::sleep_for(std::chrono::milliseconds(50));
        }
    }
}

const void* SimpleCefBrowser::GetPixelBuffer() const {
    return pixel_buffer_.get();
}

void SimpleCefBrowser::DoMessageLoopWork() {
    CefDoMessageLoopWork();
    
    // Force frame scheduling for OSR OnPaint (key fix for macOS)
    if (browser_ && browser_->GetHost()) {
        browser_->GetHost()->SendExternalBeginFrame();
    }
}

void SimpleCefBrowser::OnAfterCreated(CefRefPtr<CefBrowser> browser) {
    browser_ = browser;
    std::cout << "Browser created successfully" << std::endl;
    
    // Force initial rendering
    if (browser && browser->GetHost()) {
        browser->GetHost()->WasResized();
        browser->GetHost()->Invalidate(PET_VIEW);
    }
}

void SimpleCefBrowser::OnBeforeClose(CefRefPtr<CefBrowser> browser) {
    browser_ = nullptr;
}

void SimpleCefBrowser::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {
    rect.x = rect.y = 0;
    rect.width = width_;
    rect.height = height_;
}

void SimpleCefBrowser::OnPaint(CefRefPtr<CefBrowser> browser,
                              PaintElementType type,
                              const RectList& dirtyRects,
                              const void* buffer,
                              int width,
                              int height) {
    if (type == PET_VIEW) {
        // Copy the rendered frame to our pixel buffer
        size_t copy_size = std::min(buffer_size_, (size_t)(width * height * 4));
        memcpy(pixel_buffer_.get(), buffer, copy_size);
        
        // Log when we get actual painted content
        std::cout << "OnPaint called: " << width << "x" << height 
                  << " (" << copy_size << " bytes)" << std::endl;
    }
}

void SimpleCefBrowser::OnLoadEnd(CefRefPtr<CefBrowser> browser,
                                CefRefPtr<CefFrame> frame,
                                int httpStatusCode) {
    std::cout << "Page loaded with status: " << httpStatusCode << std::endl;
    
    // Force a paint after loading
    if (browser && browser->GetHost()) {
        browser->GetHost()->Invalidate(PET_VIEW);
        browser->GetHost()->SetFocus(true);
    }
}