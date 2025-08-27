#pragma once

#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include "include/cef_v8context.h"
#include <memory>
#include <functional>

struct VideoFrame {
    uint8_t* data;
    int width;
    int height;
    int stride;
    int64_t timestamp_us;
};

class ScreenCaptureHandler : public CefClient, 
                           public CefRenderHandler,
                           public CefV8Handler {
public:
    explicit ScreenCaptureHandler(std::function<void(const VideoFrame&)> frame_callback);
    
    // CefClient
    CefRefPtr<CefRenderHandler> GetRenderHandler() override { return this; }
    
    // CefRenderHandler - for offscreen rendering
    void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
    void OnPaint(CefRefPtr<CefBrowser> browser,
                PaintElementType type,
                const RectList& dirtyRects,
                const void* buffer,
                int width, int height) override;
    
    // CefV8Handler - for JavaScript bridge
    bool Execute(const CefString& name,
                CefRefPtr<CefV8Value> object,
                const CefV8ValueList& arguments,
                CefRefPtr<CefV8Value>& retval,
                CefString& exception) override;

private:
    std::function<void(const VideoFrame&)> frame_callback_;
    int frame_width_ = 1920;
    int frame_height_ = 1080;
    
    IMPLEMENT_REFCOUNTING(ScreenCaptureHandler);
};