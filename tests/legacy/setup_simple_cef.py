#!/usr/bin/env python3
"""
Setup script for simple_cef module.
"""

from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import os

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "simple_cef",
        [
            "src/simple_cef_browser.cpp",
            "src/python_bindings.cpp",
        ],
        include_dirs=[
            # Path to pybind11 headers
            pybind11.get_include(),
            # Path to CEF headers
            "third_party/cef",
            "include/",
        ],
        libraries=[],
        library_dirs=[],
        language='c++',
    ),
]

setup(
    name="simple_cef",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.6",
    install_requires=[
        "numpy",
        "Pillow",
    ],
)