#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "simple_cef_browser.h"

namespace py = pybind11;

PYBIND11_MODULE(simple_cef, m) {
    m.doc() = "Simple CEF headless browser for Python";

    py::class_<SimpleCefBrowser>(m, "SimpleCefBrowser")
        .def(py::init<int, int>(), "Create browser with specified width and height")
        .def("initialize", &SimpleCefBrowser::Initialize, "Initialize CEF and create browser")
        .def("shutdown", &SimpleCefBrowser::Shutdown, "Shutdown CEF and cleanup")
        .def("load_url", &SimpleCefBrowser::LoadURL, "Load a URL in the browser")
        .def("do_message_loop_work", &SimpleCefBrowser::DoMessageLoopWork, "Process CEF events")
        .def("get_width", &SimpleCefBrowser::GetWidth, "Get browser width")
        .def("get_height", &SimpleCefBrowser::GetHeight, "Get browser height")
        .def("get_buffer_size", &SimpleCefBrowser::GetBufferSize, "Get pixel buffer size")
        .def("get_pixel_buffer", [](SimpleCefBrowser &self) {
            return py::array_t<uint8_t>(
                {self.GetHeight(), self.GetWidth(), 4}, // shape: height, width, channels (BGRA)
                {self.GetWidth() * 4, 4, 1}, // strides
                static_cast<const uint8_t*>(self.GetPixelBuffer()), // data pointer
                py::cast(self) // parent object to keep alive
            );
        }, "Get pixel buffer as numpy array (height, width, 4) in BGRA format");
}