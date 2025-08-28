// Headless CEF handler implementation
#include "headless_handler.h"
#include "include/base/cef_callback.h"
#include "include/cef_app.h"
#include "include/wrapper/cef_closure_task.h"
#include "include/wrapper/cef_helpers.h"
#include <fstream>
#include <iostream>

namespace {

HeadlessHandler* g_instance = nullptr;

}  // namespace

HeadlessHandler::HeadlessHandler(int width, int height) 
    : width_(width), height_(height), is_closing_(false) {
  DCHECK(!g_instance);
  g_instance = this;
  
  buffer_size_ = width * height * 4;
  pixel_buffer_ = std::make_unique<unsigned char[]>(buffer_size_);
  
  // Initialize with white background
  for (size_t i = 0; i < buffer_size_; i += 4) {
    pixel_buffer_[i] = 255;     // B
    pixel_buffer_[i+1] = 255;   // G
    pixel_buffer_[i+2] = 255;   // R
    pixel_buffer_[i+3] = 255;   // A
  }
}

HeadlessHandler::~HeadlessHandler() {
  g_instance = nullptr;
}

// static
HeadlessHandler* HeadlessHandler::GetInstance() {
  return g_instance;
}

void HeadlessHandler::OnTitleChange(CefRefPtr<CefBrowser> browser,
                                   const CefString& title) {
  // Headless mode - no title changes needed
  std::cout << "Title: " << title.ToString() << std::endl;
}

void HeadlessHandler::OnAfterCreated(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Add to the list of existing browsers.
  browser_list_.push_back(browser);
  
  std::cout << "🎉 Browser created successfully!" << std::endl;
}

bool HeadlessHandler::DoClose(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Closing the main window requires special handling. See the DoClose()
  // documentation in the CEF header for a detailed description of this
  // process.
  if (browser_list_.size() == 1) {
    // Set a flag to indicate that the window close should be allowed.
    is_closing_ = true;
  }

  // Allow the close. For windowed browsers this will result in the OS close
  // event being sent.
  return false;
}

void HeadlessHandler::OnBeforeClose(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Remove from the list of existing browsers.
  BrowserList::iterator bit = browser_list_.begin();
  for (; bit != browser_list_.end(); ++bit) {
    if ((*bit)->IsSame(browser)) {
      browser_list_.erase(bit);
      break;
    }
  }

  if (browser_list_.empty()) {
    // All browser windows have closed. Quit the application message loop.
    CefQuitMessageLoop();
  }
}

void HeadlessHandler::OnLoadError(CefRefPtr<CefBrowser> browser,
                                 CefRefPtr<CefFrame> frame,
                                 ErrorCode errorCode,
                                 const CefString& errorText,
                                 const CefString& failedUrl) {
  CEF_REQUIRE_UI_THREAD();

  // Don't display an error for downloaded files.
  if (errorCode == ERR_ABORTED)
    return;

  std::cout << "Load error: " << errorText.ToString() << " (" << failedUrl.ToString() << ")" << std::endl;
}

void HeadlessHandler::OnLoadEnd(CefRefPtr<CefBrowser> browser,
                               CefRefPtr<CefFrame> frame,
                               int httpStatusCode) {
  std::cout << "✅ Page loaded with status: " << httpStatusCode << std::endl;
  
  // Force a paint
  if (browser && browser->GetHost()) {
    browser->GetHost()->Invalidate(PET_VIEW);
  }
}

void HeadlessHandler::GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) {
  CEF_REQUIRE_UI_THREAD();
  rect.x = rect.y = 0;
  rect.width = width_;
  rect.height = height_;
}

void HeadlessHandler::OnPaint(CefRefPtr<CefBrowser> browser,
                             PaintElementType type,
                             const RectList& dirtyRects,
                             const void* buffer,
                             int width,
                             int height) {
  CEF_REQUIRE_UI_THREAD();
  
  std::cout << "🎉 OnPaint called! " << width << "x" << height << " (" << type << ")" << std::endl;
  
  if (type == PET_VIEW) {
    // Copy the rendered frame to our pixel buffer
    size_t copy_size = std::min(buffer_size_, (size_t)(width * height * 4));
    memcpy(pixel_buffer_.get(), buffer, copy_size);
    
    // Save a frame to prove it's working
    std::ofstream file("onpaint_proof.bgra", std::ios::binary);
    file.write(static_cast<const char*>(buffer), width * height * 4);
    file.close();
    
    std::cout << "✅ Frame captured and saved!" << std::endl;
  }
}

void HeadlessHandler::CloseAllBrowsers(bool force_close) {
  if (!CefCurrentlyOn(TID_UI)) {
    // Execute on the UI thread.
    CefPostTask(TID_UI, base::BindOnce(&HeadlessHandler::CloseAllBrowsers, this,
                                       force_close));
    return;
  }

  if (browser_list_.empty())
    return;

  BrowserList::const_iterator it = browser_list_.begin();
  for (; it != browser_list_.end(); ++it)
    (*it)->GetHost()->CloseBrowser(force_close);
}

void HeadlessHandler::LoadURL(const std::string& url) {
  if (!browser_list_.empty()) {
    browser_list_.front()->GetMainFrame()->LoadURL(url);
    std::cout << "✅ Loading: " << url << std::endl;
  }
}

const unsigned char* HeadlessHandler::GetPixelBuffer() const {
  return pixel_buffer_.get();
}