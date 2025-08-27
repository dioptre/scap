#pragma once

#include "screen_capture_handler.h"
#include <memory>
#include <vector>
#include <functional>

enum class CodecType {
    VP9,    // For static areas
    H264    // For motion areas
};

struct TileRegion {
    int x, y;
    int width, height;
    CodecType codec;
    uint8_t* data;
    size_t data_size;
};

struct EncodedTile {
    int tile_id;
    int x, y;
    CodecType codec;
    std::vector<uint8_t> encoded_data;
    int64_t timestamp_us;
};

class MotionDetector {
public:
    bool HasMotion(const uint8_t* current_tile, const uint8_t* previous_tile, 
                   int width, int height, int stride);
    void UpdatePreviousFrame(const VideoFrame& frame);

private:
    std::vector<uint8_t> previous_frame_;
    int frame_width_ = 0;
    int frame_height_ = 0;
    static constexpr float kMotionThreshold = 0.05f;
};

class TiledEncoder {
public:
    explicit TiledEncoder(std::function<void(const EncodedTile&)> tile_callback);
    ~TiledEncoder();
    
    void ProcessFrame(const VideoFrame& frame);
    void SetTileSize(int width, int height) { 
        tile_width_ = width; 
        tile_height_ = height; 
    }

private:
    void InitializeEncoders();
    CodecType SelectCodecForTile(const TileRegion& tile, const VideoFrame& frame);
    EncodedTile EncodeTile(const TileRegion& tile, CodecType codec);
    
    std::function<void(const EncodedTile&)> tile_callback_;
    std::unique_ptr<MotionDetector> motion_detector_;
    
    // WebRTC encoder interfaces
    void* vp9_encoder_ = nullptr;
    void* h264_encoder_ = nullptr;
    
    int tile_width_ = 128;
    int tile_height_ = 128;
    int next_tile_id_ = 0;
};