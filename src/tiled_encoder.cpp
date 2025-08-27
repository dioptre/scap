#include "tiled_encoder.h"
#include <cstring>
#include <cmath>
#include <algorithm>
#include <iostream>

extern "C" {
#include <vpx/vpx_encoder.h>
#include <vpx/vp8cx.h>
#include <x264.h>
#include <libavcodec/avcodec.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>
}

struct VP9Encoder {
    vpx_codec_ctx_t codec;
    vpx_codec_enc_cfg_t cfg;
    vpx_image_t raw_image;
    bool initialized = false;
};

struct H264Encoder {
    x264_t* encoder;
    x264_param_t param;
    x264_picture_t pic_in;
    x264_picture_t pic_out;
    bool initialized = false;
};

bool MotionDetector::HasMotion(const uint8_t* current_tile, const uint8_t* previous_tile,
                              int width, int height, int stride) {
    if (!previous_tile) return true;
    
    int total_pixels = width * height;
    int changed_pixels = 0;
    
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            int offset = y * stride + x * 4; // BGRA
            
            // Simple RGB difference
            int r_diff = abs(current_tile[offset + 2] - previous_tile[offset + 2]);
            int g_diff = abs(current_tile[offset + 1] - previous_tile[offset + 1]);
            int b_diff = abs(current_tile[offset + 0] - previous_tile[offset + 0]);
            
            if (r_diff + g_diff + b_diff > 30) {
                changed_pixels++;
            }
        }
    }
    
    return (static_cast<float>(changed_pixels) / total_pixels) > kMotionThreshold;
}

void MotionDetector::UpdatePreviousFrame(const VideoFrame& frame) {
    if (frame_width_ != frame.width || frame_height_ != frame.height) {
        frame_width_ = frame.width;
        frame_height_ = frame.height;
        previous_frame_.resize(frame.width * frame.height * 4);
    }
    
    std::memcpy(previous_frame_.data(), frame.data, 
                frame.width * frame.height * 4);
}

TiledEncoder::TiledEncoder(std::function<void(const EncodedTile&)> tile_callback)
    : tile_callback_(std::move(tile_callback))
    , motion_detector_(std::make_unique<MotionDetector>()) {
    InitializeEncoders();
}

TiledEncoder::~TiledEncoder() {
    if (vp9_encoder_) {
        VP9Encoder* encoder = static_cast<VP9Encoder*>(vp9_encoder_);
        if (encoder->initialized) {
            vpx_codec_destroy(&encoder->codec);
            vpx_img_free(&encoder->raw_image);
        }
        delete encoder;
    }
    
    if (h264_encoder_) {
        H264Encoder* encoder = static_cast<H264Encoder*>(h264_encoder_);
        if (encoder->initialized) {
            x264_encoder_close(encoder->encoder);
        }
        delete encoder;
    }
}

void TiledEncoder::InitializeEncoders() {
    // Initialize VP9 encoder
    VP9Encoder* vp9 = new VP9Encoder();
    vpx_codec_enc_config_default(vpx_codec_vp9_cx(), &vp9->cfg, 0);
    
    vp9->cfg.g_w = tile_width_;
    vp9->cfg.g_h = tile_height_;
    vp9->cfg.g_timebase.num = 1;
    vp9->cfg.g_timebase.den = 30;
    vp9->cfg.rc_target_bitrate = 500; // 500 kbps
    vp9->cfg.g_error_resilient = VPX_ERROR_RESILIENT_DEFAULT;
    vp9->cfg.g_lag_in_frames = 0;
    vp9->cfg.kf_mode = VPX_KF_DISABLED;
    
    if (vpx_codec_enc_init(&vp9->codec, vpx_codec_vp9_cx(), &vp9->cfg, 0)) {
        std::cerr << "Failed to initialize VP9 encoder" << std::endl;
        delete vp9;
        return;
    }
    
    if (!vpx_img_alloc(&vp9->raw_image, VPX_IMG_FMT_I420, tile_width_, tile_height_, 1)) {
        std::cerr << "Failed to allocate VP9 image" << std::endl;
        vpx_codec_destroy(&vp9->codec);
        delete vp9;
        return;
    }
    
    vp9->initialized = true;
    vp9_encoder_ = vp9;
    
    // Initialize H.264 encoder
    H264Encoder* h264 = new H264Encoder();
    x264_param_default_preset(&h264->param, "ultrafast", "zerolatency");
    
    h264->param.i_width = tile_width_;
    h264->param.i_height = tile_height_;
    h264->param.i_fps_num = 30;
    h264->param.i_fps_den = 1;
    h264->param.rc.i_bitrate = 1000; // 1000 kbps
    h264->param.i_keyint_max = 30;
    h264->param.b_intra_refresh = 1;
    h264->param.b_annexb = 1;
    
    if (x264_param_apply_profile(&h264->param, "baseline") < 0) {
        std::cerr << "Failed to apply H.264 profile" << std::endl;
        delete h264;
        return;
    }
    
    h264->encoder = x264_encoder_open(&h264->param);
    if (!h264->encoder) {
        std::cerr << "Failed to open H.264 encoder" << std::endl;
        delete h264;
        return;
    }
    
    if (x264_picture_alloc(&h264->pic_in, X264_CSP_I420, tile_width_, tile_height_) < 0) {
        std::cerr << "Failed to allocate H.264 picture" << std::endl;
        x264_encoder_close(h264->encoder);
        delete h264;
        return;
    }
    
    h264->initialized = true;
    h264_encoder_ = h264;
}

void TiledEncoder::ProcessFrame(const VideoFrame& frame) {
    int tiles_x = (frame.width + tile_width_ - 1) / tile_width_;
    int tiles_y = (frame.height + tile_height_ - 1) / tile_height_;
    
    for (int ty = 0; ty < tiles_y; ++ty) {
        for (int tx = 0; tx < tiles_x; ++tx) {
            TileRegion tile;
            tile.x = tx * tile_width_;
            tile.y = ty * tile_height_;
            tile.width = std::min(tile_width_, frame.width - tile.x);
            tile.height = std::min(tile_height_, frame.height - tile.y);
            
            // Extract tile data
            tile.data_size = tile.width * tile.height * 4;
            auto tile_data = std::make_unique<uint8_t[]>(tile.data_size);
            
            for (int y = 0; y < tile.height; ++y) {
                const uint8_t* src = frame.data + 
                    ((tile.y + y) * frame.stride) + (tile.x * 4);
                uint8_t* dst = tile_data.get() + (y * tile.width * 4);
                std::memcpy(dst, src, tile.width * 4);
            }
            tile.data = tile_data.get();
            
            // Select codec based on motion
            CodecType codec = SelectCodecForTile(tile, frame);
            
            // Encode tile
            EncodedTile encoded = EncodeTile(tile, codec);
            encoded.tile_id = next_tile_id_++;
            encoded.x = tile.x;
            encoded.y = tile.y;
            encoded.timestamp_us = frame.timestamp_us;
            
            // Send to callback
            tile_callback_(encoded);
        }
    }
    
    motion_detector_->UpdatePreviousFrame(frame);
}

CodecType TiledEncoder::SelectCodecForTile(const TileRegion& tile, const VideoFrame& frame) {
    // Check if this tile has motion compared to previous frame
    const uint8_t* previous_tile = nullptr; 
    
    bool has_motion = motion_detector_->HasMotion(tile.data, previous_tile,
                                                 tile.width, tile.height, tile.width * 4);
    
    return has_motion ? CodecType::H264 : CodecType::VP9;
}

void ConvertBGRAToI420(const uint8_t* bgra_data, int width, int height, 
                       uint8_t* y_plane, uint8_t* u_plane, uint8_t* v_plane) {
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int bgra_idx = (y * width + x) * 4;
            uint8_t b = bgra_data[bgra_idx + 0];
            uint8_t g = bgra_data[bgra_idx + 1];
            uint8_t r = bgra_data[bgra_idx + 2];
            
            // Convert RGB to YUV
            int y_val = (66 * r + 129 * g + 25 * b + 128) >> 8) + 16;
            y_plane[y * width + x] = std::clamp(y_val, 0, 255);
            
            if (y % 2 == 0 && x % 2 == 0) {
                int u_val = ((-38 * r - 74 * g + 112 * b + 128) >> 8) + 128;
                int v_val = ((112 * r - 94 * g - 18 * b + 128) >> 8) + 128;
                
                int uv_idx = (y / 2) * (width / 2) + (x / 2);
                u_plane[uv_idx] = std::clamp(u_val, 0, 255);
                v_plane[uv_idx] = std::clamp(v_val, 0, 255);
            }
        }
    }
}

EncodedTile TiledEncoder::EncodeTile(const TileRegion& tile, CodecType codec) {
    EncodedTile result;
    result.codec = codec;
    
    if (codec == CodecType::VP9 && vp9_encoder_) {
        VP9Encoder* encoder = static_cast<VP9Encoder*>(vp9_encoder_);
        
        // Convert BGRA to I420
        ConvertBGRAToI420(tile.data, tile.width, tile.height,
                         encoder->raw_image.planes[VPX_PLANE_Y],
                         encoder->raw_image.planes[VPX_PLANE_U],
                         encoder->raw_image.planes[VPX_PLANE_V]);
        
        const vpx_codec_cx_pkt_t* pkt;
        vpx_codec_iter_t iter = NULL;
        
        if (vpx_codec_encode(&encoder->codec, &encoder->raw_image, 0, 1, 0, VPX_DL_REALTIME)) {
            std::cerr << "VP9 encode failed" << std::endl;
            return result;
        }
        
        while ((pkt = vpx_codec_get_cx_data(&encoder->codec, &iter))) {
            if (pkt->kind == VPX_CODEC_CX_FRAME_PKT) {
                result.encoded_data.assign(
                    static_cast<const uint8_t*>(pkt->data.frame.buf),
                    static_cast<const uint8_t*>(pkt->data.frame.buf) + pkt->data.frame.sz
                );
                break;
            }
        }
    }
    else if (codec == CodecType::H264 && h264_encoder_) {
        H264Encoder* encoder = static_cast<H264Encoder*>(h264_encoder_);
        
        // Convert BGRA to I420
        ConvertBGRAToI420(tile.data, tile.width, tile.height,
                         encoder->pic_in.img.plane[0],
                         encoder->pic_in.img.plane[1],
                         encoder->pic_in.img.plane[2]);
        
        x264_nal_t* nals;
        int num_nals;
        int frame_size = x264_encoder_encode(encoder->encoder, &nals, &num_nals,
                                           &encoder->pic_in, &encoder->pic_out);
        
        if (frame_size > 0) {
            for (int i = 0; i < num_nals; i++) {
                result.encoded_data.insert(result.encoded_data.end(),
                                         nals[i].p_payload,
                                         nals[i].p_payload + nals[i].i_payload);
            }
        }
    }
    
    return result;
}