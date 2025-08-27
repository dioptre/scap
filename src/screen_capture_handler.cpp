#include "screen_capture_handler.h"
#include "include/cef_browser.h"
#include "include/cef_frame.h"
#include <iostream>

ScreenCaptureHandler::ScreenCaptureHandler(std::function<void(const VideoFrame&)> frame_callback)
    : frame_callback_(std::move(frame_callback)) {}

void ScreenCaptureHandler::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {
    rect = CefRect(0, 0, frame_width_, frame_height_);
}

void ScreenCaptureHandler::OnPaint(CefRefPtr<CefBrowser> browser,
                                  PaintElementType type,
                                  const RectList& dirtyRects,
                                  const void* buffer,
                                  int width, int height) {
    if (type != PET_VIEW || !frame_callback_) return;
    
    VideoFrame frame;
    frame.data = const_cast<uint8_t*>(static_cast<const uint8_t*>(buffer));
    frame.width = width;
    frame.height = height;
    frame.stride = width * 4; // BGRA format
    frame.timestamp_us = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::high_resolution_clock::now().time_since_epoch()).count();
    
    frame_callback_(frame);
}

bool ScreenCaptureHandler::Execute(const CefString& name,
                                  CefRefPtr<CefV8Value> object,
                                  const CefV8ValueList& arguments,
                                  CefRefPtr<CefV8Value>& retval,
                                  CefString& exception) {
    
    if (name == "startScreenCapture") {
        // Inject WebRTC screen capture JavaScript
        auto context = CefV8Context::GetCurrentContext();
        auto browser = context->GetBrowser();
        auto frame = browser->GetMainFrame();
        
        std::string js_code = R"(
            async function startCapture() {
                try {
                    const stream = await navigator.mediaDevices.getDisplayMedia({
                        video: {
                            mediaSource: 'browser',
                            frameRate: 60,
                            width: 1920,
                            height: 1080
                        }
                    });
                    
                    const track = stream.getVideoTracks()[0];
                    const processor = new MediaStreamTrackProcessor({track});
                    const reader = processor.readable.getReader();
                    
                    while (true) {
                        const {value: frame, done} = await reader.read();
                        if (done) break;
                        
                        // Send frame to C++ via canvas
                        const canvas = document.getElementById('capture-canvas');
                        const ctx = canvas.getContext('2d');
                        canvas.width = frame.displayWidth;
                        canvas.height = frame.displayHeight;
                        ctx.drawImage(frame, 0, 0);
                        
                        frame.close();
                    }
                } catch (err) {
                    console.error('Screen capture failed:', err);
                }
            }
            startCapture();
        )";
        
        frame->ExecuteJavaScript(js_code, frame->GetURL(), 0);
        retval = CefV8Value::CreateBool(true);
        return true;
    }
    
    return false;
}