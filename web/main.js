class ScreenCaptureTilingSystem {
    constructor() {
        this.ws = null;
        this.isCapturing = false;
        this.mediaStream = null;
        this.canvas = document.getElementById('displayCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.wasmDecoder = null;
        
        // Statistics
        this.stats = {
            frameRate: 0,
            frameCount: 0,
            lastFrameTime: Date.now(),
            vp9TileCount: 0,
            h264TileCount: 0,
            totalTileCount: 0
        };
        
        this.tileOverlays = [];
        this.frameId = 0;
        
        this.initializeUI();
        this.connectWebSocket();
        this.loadWasmDecoder();
    }
    
    async loadWasmDecoder() {
        try {
            // Load the WASM module
            const Module = await createWasmModule();
            this.wasmDecoder = new Module.WasmTileDecoder();
            this.log('WASM decoder initialized successfully', 'success');
        } catch (error) {
            this.log(`Failed to load WASM decoder: ${error.message}`, 'error');
        }
    }
    
    initializeUI() {
        document.getElementById('startBtn').addEventListener('click', () => this.startCapture());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopCapture());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearDisplay());
        
        // Update stats every second
        setInterval(() => this.updateStats(), 1000);
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            this.log('WebSocket connected', 'success');
            document.getElementById('connectionStatus').textContent = 'Connected';
            
            // Send ping to keep connection alive
            setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.ws.onclose = () => {
            this.log('WebSocket disconnected', 'error');
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            this.log(`WebSocket error: ${error}`, 'error');
        };
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'tiles':
                this.renderTiles(message.tiles, message.frame_id);
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                this.log(`Unknown message type: ${message.type}`, 'error');
        }
    }
    
    async startCapture() {
        try {
            this.mediaStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    mediaSource: 'browser',
                    frameRate: 30,
                    width: 1920,
                    height: 1080
                }
            });
            
            const track = this.mediaStream.getVideoTracks()[0];
            
            // Use MediaStreamTrackProcessor for frame-by-frame access
            if ('MediaStreamTrackProcessor' in window) {
                const processor = new MediaStreamTrackProcessor({ track });
                const reader = processor.readable.getReader();
                
                this.isCapturing = true;
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                this.log('Screen capture started using MediaStreamTrackProcessor', 'success');
                this.processFrames(reader);
            } else {
                // Fallback to canvas capture
                this.log('MediaStreamTrackProcessor not supported, using canvas fallback', 'info');
                this.startCanvasCapture();
            }
            
        } catch (error) {
            this.log(`Screen capture failed: ${error.message}`, 'error');
        }
    }
    
    async processFrames(reader) {
        try {
            while (this.isCapturing) {
                const { value: frame, done } = await reader.read();
                if (done) break;
                
                await this.captureFrame(frame);
                frame.close();
                
                // Limit frame rate to avoid overwhelming the system
                await new Promise(resolve => setTimeout(resolve, 33)); // ~30 FPS
            }
        } catch (error) {
            this.log(`Frame processing error: ${error.message}`, 'error');
        }
    }
    
    startCanvasCapture() {
        const video = document.createElement('video');
        video.srcObject = this.mediaStream;
        video.play();
        
        video.onloadedmetadata = () => {
            const captureCanvas = document.createElement('canvas');
            const captureCtx = captureCanvas.getContext('2d');
            
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;
            
            const captureFrame = () => {
                if (!this.isCapturing) return;
                
                captureCtx.drawImage(video, 0, 0);
                const imageData = captureCtx.getImageData(0, 0, captureCanvas.width, captureCanvas.height);
                
                this.sendFrameData(imageData.data.buffer, captureCanvas.width, captureCanvas.height);
                
                requestAnimationFrame(captureFrame);
            };
            
            captureFrame();
        };
    }
    
    async captureFrame(videoFrame) {
        // Create canvas to extract pixel data
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = videoFrame.displayWidth;
        tempCanvas.height = videoFrame.displayHeight;
        
        tempCtx.drawImage(videoFrame, 0, 0);
        const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        
        this.sendFrameData(imageData.data.buffer, tempCanvas.width, tempCanvas.height);
    }
    
    sendFrameData(frameBuffer, width, height) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        // Convert ArrayBuffer to base64
        const uint8Array = new Uint8Array(frameBuffer);
        const base64Data = this.arrayBufferToBase64(uint8Array);
        
        const message = {
            type: 'frame',
            frame_id: this.frameId++,
            data: base64Data,
            width: width,
            height: height,
            timestamp: Date.now()
        };
        
        this.ws.send(JSON.stringify(message));
        this.stats.frameCount++;
    }
    
    async renderTiles(tiles, frameId) {
        if (!this.wasmDecoder) {
            this.log('WASM decoder not ready', 'error');
            return;
        }
        
        this.clearTileOverlays();
        
        let vp9Count = 0;
        let h264Count = 0;
        
        try {
            // Decode tiles using WASM
            const decodedTiles = this.wasmDecoder.decodeTiles(tiles);
            
            for (let i = 0; i < decodedTiles.size(); i++) {
                const tile = decodedTiles.get(i);
                const x = tile.x;
                const y = tile.y;
                const width = tile.width;
                const height = tile.height;
                const pixelData = tile.data;
                
                // Create ImageData and draw to canvas
                const imageData = new ImageData(new Uint8ClampedArray(pixelData), width, height);
                this.ctx.putImageData(imageData, x, y);
                
                // Add tile overlay for visualization
                const codecType = tiles[i].codec === 0 ? 'vp9' : 'h264';
                this.addTileOverlay(x, y, width, height, codecType);
                
                if (codecType === 'vp9') vp9Count++;
                else h264Count++;
            }
            
        } catch (error) {
            this.log(`Tile rendering error: ${error.message}`, 'error');
            
            // Fallback: render tiles as colored rectangles
            tiles.forEach(tile => {
                const color = tile.codec === 0 ? '#00ff00' : '#ff0000'; // Green for VP9, Red for H.264
                this.ctx.fillStyle = color;
                this.ctx.fillRect(tile.x, tile.y, tile.width || 128, tile.height || 128);
                
                if (tile.codec === 0) vp9Count++;
                else h264Count++;
            });
        }
        
        // Update statistics
        this.stats.totalTileCount = tiles.length;
        this.stats.vp9TileCount = vp9Count;
        this.stats.h264TileCount = h264Count;
        
        this.log(`Rendered frame ${frameId} with ${tiles.length} tiles (VP9: ${vp9Count}, H.264: ${h264Count})`, 'info');
    }
    
    addTileOverlay(x, y, width, height, codecType) {
        const overlay = document.createElement('div');
        overlay.className = `tile-overlay ${codecType}`;
        overlay.style.left = `${x}px`;
        overlay.style.top = `${y}px`;
        overlay.style.width = `${width}px`;
        overlay.style.height = `${height}px`;
        
        document.getElementById('canvasContainer').appendChild(overlay);
        this.tileOverlays.push(overlay);
        
        // Remove overlay after 2 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 2000);
    }
    
    clearTileOverlays() {
        this.tileOverlays.forEach(overlay => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        });
        this.tileOverlays = [];
    }
    
    stopCapture() {
        this.isCapturing = false;
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        
        this.log('Screen capture stopped', 'info');
    }
    
    clearDisplay() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.clearTileOverlays();
        this.log('Display cleared', 'info');
    }
    
    updateStats() {
        const now = Date.now();
        const elapsed = (now - this.stats.lastFrameTime) / 1000;
        this.stats.frameRate = Math.round(this.stats.frameCount / elapsed);
        
        document.getElementById('frameRate').textContent = this.stats.frameRate;
        document.getElementById('tileCount').textContent = this.stats.totalTileCount;
        document.getElementById('vp9Count').textContent = this.stats.vp9TileCount;
        document.getElementById('h264Count').textContent = this.stats.h264TileCount;
        
        // Reset counters
        this.stats.frameCount = 0;
        this.stats.lastFrameTime = now;
    }
    
    log(message, level = 'info') {
        const logContainer = document.getElementById('logContainer');
        const entry = document.createElement('div');
        entry.className = `log-entry ${level}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Keep only last 100 log entries
        while (logContainer.children.length > 100) {
            logContainer.removeChild(logContainer.firstChild);
        }
        
        console.log(`[ScreenCapture] ${message}`);
    }
    
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }
}

// Mock WASM module loader (replace with actual WASM loader)
async function createWasmModule() {
    // This would load the actual WASM module
    // For now, return a mock implementation
    return {
        WasmTileDecoder: class {
            decodeTiles(tiles) {
                // Mock implementation that returns the tiles as-is
                return {
                    size: () => tiles.length,
                    get: (i) => ({
                        x: tiles[i].x,
                        y: tiles[i].y,
                        width: tiles[i].width || 128,
                        height: tiles[i].height || 128,
                        data: new Uint8Array(128 * 128 * 4) // Mock RGBA data
                    })
                };
            }
        }
    };
}

// Initialize the system when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.screenCaptureSystem = new ScreenCaptureTilingSystem();
});