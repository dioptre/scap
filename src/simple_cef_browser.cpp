#include "simple_cef_browser.h"
#include "include/cef_sandbox_mac.h"
#include <iostream>

SimpleCefBrowser::SimpleCefBrowser(int width, int height) 
    : width_(width), height_(height), is_initialized_(false) {
    buffer_size_ = width * height * 4; // BGRA format
    pixel_buffer_ = std::make_unique<unsigned char[]>(buffer_size_);
    memset(pixel_buffer_.get(), 0, buffer_size_);
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

    // CEF settings
    CefSettings settings;
    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;
    settings.log_severity = LOGSEVERITY_INFO;
    
    // Initialize CEF
    CefRefPtr<CefApp> app(new SimpleCefApp());
    if (!CefInitialize(CefMainArgs(), settings, app.get(), nullptr)) {
        std::cerr << "Failed to initialize CEF" << std::endl;
        return false;
    }

    // Create browser window info
    CefWindowInfo window_info;
    window_info.SetAsWindowless(0); // 0 = no parent window for headless

    // Browser settings
    CefBrowserSettings browser_settings;
    browser_settings.windowless_frame_rate = 30; // 30 FPS

    // Create browser
    CefBrowserHost::CreateBrowser(window_info, this, "about:blank", browser_settings, nullptr, nullptr);
    
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
        browser_->GetMainFrame()->LoadURL(url);
    }
}

const void* SimpleCefBrowser::GetPixelBuffer() const {
    return pixel_buffer_.get();
}

void SimpleCefBrowser::DoMessageLoopWork() {
    CefDoMessageLoopWork();
}

void SimpleCefBrowser::OnAfterCreated(CefRefPtr<CefBrowser> browser) {
    browser_ = browser;
    std::cout << "Browser created successfully" << std::endl;
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
    }
}

void SimpleCefBrowser::OnLoadEnd(CefRefPtr<CefBrowser> browser,
                                CefRefPtr<CefFrame> frame,
                                int httpStatusCode) {
    std::cout << "Page loaded with status: " << httpStatusCode << std::endl;
}