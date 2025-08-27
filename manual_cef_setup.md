# Manual CEF Setup

If the automated CEF download fails, follow these steps:

## Step 1: Browse Available CEF Builds
Go to: https://cef-builds.spotifycdn.com/

## Step 2: Find macOS Build
Look for a file matching this pattern:
`cef_binary_*_macosx64.tar.bz2`

Recent versions:
- `cef_binary_120.1.10+g3ce3184+chromium-120.0.6099.129_macosx64.tar.bz2`
- `cef_binary_119.4.7+g55e15c8+chromium-119.0.6045.199_macosx64.tar.bz2`
- `cef_binary_118.7.1+g99817d2+chromium-118.0.5993.117_macosx64.tar.bz2`

## Step 3: Download and Extract
```bash
cd third_party/
wget [CEF_BUILD_URL]
tar -xjf cef_binary_*_macosx64.tar.bz2
mv cef_binary_*_macosx64 cef
rm cef_binary_*_macosx64.tar.bz2
```

## Step 4: Build CEF Wrapper
```bash
cd cef/
mkdir -p build
cd build/
cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release ..
make -j$(sysctl -n hw.ncpu) libcef_dll_wrapper
```

## Alternative: Use Homebrew CEF (Experimental)
```bash
# Warning: May not be compatible
brew install cef
```

Then modify CMakeLists.txt to point to Homebrew CEF location.