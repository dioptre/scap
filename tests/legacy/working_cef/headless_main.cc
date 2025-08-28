// Headless CEF main based on working cefsimple
#include "include/cef_app.h"
#include "include/cef_command_line.h"
#include "include/wrapper/cef_helpers.h"
#include "include/wrapper/cef_library_loader.h"
#include "headless_handler.h"
#include "simple_app.h"

#include <iostream>
#include <thread>
#include <chrono>

// Entry point function for the browser process.
int main(int argc, char* argv[]) {
  std::cout << "🧪 Starting Headless CEF Browser (based on working cefsimple)" << std::endl;
  
  // Load the CEF framework library at runtime instead of linking directly
  // as required by the macOS sandbox implementation.
  CefScopedLibraryLoader library_loader;
  if (!library_loader.LoadInMain()) {
    std::cerr << "❌ Failed to load CEF library" << std::endl;
    return 1;
  }
  std::cout << "✅ CEF library loaded" << std::endl;

  // Provide CEF with command-line arguments.
  CefMainArgs main_args(argc, argv);

  // SimpleApp implements application-level callbacks for the browser process.
  // It will create the first browser instance in OnContextInitialized() after
  // CEF has been initialized. 
  CefRefPtr<SimpleApp> app(new SimpleApp);

  // CEF applications have multiple sub-processes (render, plugin, GPU, etc)
  // that share the same executable. This function checks the command-line and,
  // if this is a sub-process, executes the appropriate logic.
  int exit_code = CefExecuteProcess(main_args, app, nullptr);
  if (exit_code >= 0) {
    // The sub-process has completed so return here.
    std::cout << "Subprocess completed: " << exit_code << std::endl;
    return exit_code;
  }

  std::cout << "✅ Main process continuing..." << std::endl;

  // Specify CEF global settings here.
  CefSettings settings;

  // Use multi-threaded message loop for better compatibility
  settings.multi_threaded_message_loop = false;
  settings.no_sandbox = true;
  settings.windowless_rendering_enabled = true;

  // Initialize CEF.
  if (!CefInitialize(main_args, settings, app.get(), nullptr)) {
    std::cerr << "❌ CefInitialize failed" << std::endl;
    return 1;
  }
  std::cout << "✅ CEF initialized successfully!" << std::endl;

  // Create the headless browser
  HeadlessHandler* handler = new HeadlessHandler(900, 600);
  
  // Information used when creating the native window.
  CefWindowInfo window_info;
  window_info.SetAsWindowless(0);  // Headless mode

  // Specify CEF browser settings here.
  CefBrowserSettings browser_settings;
  browser_settings.windowless_frame_rate = 10;

  // Create the first browser window.
  std::cout << "🌐 Creating headless browser..." << std::endl;
  CefBrowserHost::CreateBrowser(window_info, handler, "data:text/html,<h1 style='color:red;font-size:100px;'>CEF WORKING!</h1>", browser_settings, nullptr, nullptr);

  // Run the CEF message loop. This will block until CefQuitMessageLoop() is
  // called.
  std::cout << "🔄 Running CEF message loop..." << std::endl;
  
  // Run for a limited time to test
  for (int i = 0; i < 100; ++i) {
    CefDoMessageLoopWork();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }

  // Shut down CEF.
  handler->CloseAllBrowsers(false);
  
  // Wait for browsers to close
  for (int i = 0; i < 50; ++i) {
    CefDoMessageLoopWork();
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
  }
  
  CefShutdown();
  std::cout << "✅ CEF shutdown complete" << std::endl;

  return 0;
}