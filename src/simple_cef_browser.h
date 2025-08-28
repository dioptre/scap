#ifndef SIMPLE_CEF_BROWSER_H
#define SIMPLE_CEF_BROWSER_H

#include "include/cef_app.h"
#include "include/cef_browser.h"
#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include <memory>
#include <functional>

class SimpleCefBrowser : public CefClient,
                        public CefLifeSpanHandler,
                        public CefRenderHandler,
                        public CefLoadHandler {
public:
    SimpleCefBrowser(int width, int height);
    ~SimpleCefBrowser();

    // Initialize CEF and create browser
    bool Initialize();
    void Shutdown();
    
    // Navigation
    void LoadURL(const std::string& url);
    
    // Access to raw pixels
    const void* GetPixelBuffer() const;
    int GetWidth() const { return width_; }
    int GetHeight() const { return height_; }
    size_t GetBufferSize() const { return buffer_size_; }
    
    // Process CEF events
    void DoMessageLoopWork();

    // CefClient methods
    CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
    CefRefPtr<CefRenderHandler> GetRenderHandler() override { return this; }
    CefRefPtr<CefLoadHandler> GetLoadHandler() override { return this; }

    // CefLifeSpanHandler methods
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override;
    void OnBeforeClose(CefRefPtr<CefBrowser> browser) override;

    // CefRenderHandler methods
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser,
                 PaintElementType type,
                 const RectList& dirtyRects,
                 const void* buffer,
                 int width,
                 int height) override;

    // CefLoadHandler methods
    void OnLoadEnd(CefRefPtr<CefBrowser> browser,
                   CefRefPtr<CefFrame> frame,
                   int httpStatusCode) override;

private:
    int width_;
    int height_;
    size_t buffer_size_;
    std::unique_ptr<unsigned char[]> pixel_buffer_;
    CefRefPtr<CefBrowser> browser_;
    bool is_initialized_;
    
    IMPLEMENT_REFCOUNTING(SimpleCefBrowser);
};

// Simple app class for CEF initialization
class SimpleCefApp : public CefApp {
public:
    SimpleCefApp() {}

private:
    IMPLEMENT_REFCOUNTING(SimpleCefApp);
};

#endif // SIMPLE_CEF_BROWSER_H