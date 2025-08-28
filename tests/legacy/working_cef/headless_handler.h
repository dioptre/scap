// Headless CEF handler based on working cefsimple
#ifndef CEF_HEADLESS_HANDLER_H_
#define CEF_HEADLESS_HANDLER_H_

#include "include/cef_client.h"
#include "include/cef_render_handler.h"
#include "include/wrapper/cef_helpers.h"
#include <memory>
#include <list>

class HeadlessHandler : public CefClient,
                        public CefDisplayHandler,
                        public CefLifeSpanHandler,
                        public CefLoadHandler,
                        public CefRenderHandler {
 public:
  explicit HeadlessHandler(int width, int height);
  ~HeadlessHandler();

  // Provide access to the single global instance of this object.
  static HeadlessHandler* GetInstance();

  // CefClient methods:
  virtual CefRefPtr<CefDisplayHandler> GetDisplayHandler() override {
    return this;
  }
  virtual CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override {
    return this;
  }
  virtual CefRefPtr<CefLoadHandler> GetLoadHandler() override { 
    return this; 
  }
  virtual CefRefPtr<CefRenderHandler> GetRenderHandler() override {
    return this;
  }

  // CefDisplayHandler methods:
  virtual void OnTitleChange(CefRefPtr<CefBrowser> browser,
                             const CefString& title) override;

  // CefLifeSpanHandler methods:
  virtual void OnAfterCreated(CefRefPtr<CefBrowser> browser) override;
  virtual bool DoClose(CefRefPtr<CefBrowser> browser) override;
  virtual void OnBeforeClose(CefRefPtr<CefBrowser> browser) override;

  // CefLoadHandler methods:
  virtual void OnLoadError(CefRefPtr<CefBrowser> browser,
                           CefRefPtr<CefFrame> frame,
                           ErrorCode errorCode,
                           const CefString& errorText,
                           const CefString& failedUrl) override;
  
  virtual void OnLoadEnd(CefRefPtr<CefBrowser> browser,
                         CefRefPtr<CefFrame> frame,
                         int httpStatusCode) override;

  // CefRenderHandler methods (CRITICAL for headless)
  virtual void GetViewRect(CefRefPtr<CefBrowser> browser, CefRect& rect) override;
  virtual void OnPaint(CefRefPtr<CefBrowser> browser,
                       PaintElementType type,
                       const RectList& dirtyRects,
                       const void* buffer,
                       int width,
                       int height) override;

  // Request that all existing browser windows close.
  void CloseAllBrowsers(bool force_close);
  
  // Load URL
  void LoadURL(const std::string& url);
  
  // Get pixel data
  const unsigned char* GetPixelBuffer() const;
  int GetWidth() const { return width_; }
  int GetHeight() const { return height_; }

  bool IsClosing() const { return is_closing_; }

 private:
  int width_;
  int height_;
  std::unique_ptr<unsigned char[]> pixel_buffer_;
  size_t buffer_size_;

  // List of existing browser windows. Only accessed on the CEF UI thread.
  typedef std::list<CefRefPtr<CefBrowser>> BrowserList;
  BrowserList browser_list_;

  bool is_closing_;

  // Include the default reference counting implementation.
  IMPLEMENT_REFCOUNTING(HeadlessHandler);
};

#endif  // CEF_HEADLESS_HANDLER_H_