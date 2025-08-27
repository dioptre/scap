#include <emscripten.h>
#include <emscripten/bind.h>
#include <vector>
#include <memory>
#include <cstring>

extern "C" {
#include <vpx/vpx_decoder.h>
#include <vpx/vp8dx.h>
#include <libavcodec/avcodec.h>
#include <libavutil/imgutils.h>
#include <libswscale/swscale.h>
}

struct VP9Decoder {
    vpx_codec_ctx_t codec;
    bool initialized = false;
};

struct H264Decoder {
    AVCodecContext* codec_ctx;
    const AVCodec* codec;
    AVFrame* frame;
    AVPacket* packet;
    SwsContext* sws_ctx;
    bool initialized = false;
};

class WasmTileDecoder {
public:
    WasmTileDecoder() {
        InitializeDecoders();
    }
    
    ~WasmTileDecoder() {
        if (vp9_decoder_) {
            VP9Decoder* decoder = static_cast<VP9Decoder*>(vp9_decoder_);
            if (decoder->initialized) {
                vpx_codec_destroy(&decoder->codec);
            }
            delete decoder;
        }
        
        if (h264_decoder_) {
            H264Decoder* decoder = static_cast<H264Decoder*>(h264_decoder_);
            if (decoder->initialized) {
                avcodec_free_context(&decoder->codec_ctx);
                av_frame_free(&decoder->frame);
                av_packet_free(&decoder->packet);
                if (decoder->sws_ctx) {
                    sws_freeContext(decoder->sws_ctx);
                }
            }
            delete decoder;
        }
    }
    
    // Decode a single tile and return raw RGBA data
    std::vector<uint8_t> decodeTile(const std::vector<uint8_t>& encoded_data, 
                                   int codec_type) {
        if (codec_type == 0) { // VP9
            return decodeVP9Tile(encoded_data);
        } else { // H.264
            return decodeH264Tile(encoded_data);
        }
    }
    
    // Batch decode multiple tiles
    emscripten::val decodeTiles(emscripten::val tile_array) {
        auto result = emscripten::val::array();
        int length = tile_array["length"].as<int>();
        
        for (int i = 0; i < length; i++) {
            auto tile = tile_array[i];
            
            // Extract tile data
            auto encoded_data_val = tile["data"];
            std::vector<uint8_t> encoded_data;
            
            int data_length = encoded_data_val["length"].as<int>();
            encoded_data.resize(data_length);
            
            for (int j = 0; j < data_length; j++) {
                encoded_data[j] = encoded_data_val[j].as<uint8_t>();
            }
            
            int codec_type = tile["codec"].as<int>();
            int x = tile["x"].as<int>();
            int y = tile["y"].as<int>();
            
            auto decoded_data = decodeTile(encoded_data, codec_type);
            
            if (!decoded_data.empty()) {
                auto tile_result = emscripten::val::object();
                tile_result.set("x", x);
                tile_result.set("y", y);
                tile_result.set("width", 128);
                tile_result.set("height", 128);
                
                // Convert to JavaScript Uint8Array
                auto js_array = emscripten::val::global("Uint8Array").new_(decoded_data.size());
                emscripten::val memory = emscripten::val::module_property("HEAPU8");
                js_array.call<void>("set", memory.call<emscripten::val>("subarray", 
                    reinterpret_cast<uintptr_t>(decoded_data.data()),
                    reinterpret_cast<uintptr_t>(decoded_data.data()) + decoded_data.size()));
                
                tile_result.set("data", js_array);
                result.call<void>("push", tile_result);
            }
        }
        
        return result;
    }

private:
    void InitializeDecoders() {
        // Initialize VP9 decoder
        VP9Decoder* vp9 = new VP9Decoder();
        if (vpx_codec_dec_init(&vp9->codec, vpx_codec_vp9_dx(), NULL, 0)) {
            std::cerr << "Failed to initialize VP9 decoder" << std::endl;
            delete vp9;
        } else {
            vp9->initialized = true;
            vp9_decoder_ = vp9;
        }
        
        // Initialize H.264 decoder  
        H264Decoder* h264 = new H264Decoder();
        h264->codec = avcodec_find_decoder(AV_CODEC_ID_H264);
        if (!h264->codec) {
            std::cerr << "H.264 decoder not found" << std::endl;
            delete h264;
            return;
        }
        
        h264->codec_ctx = avcodec_alloc_context3(h264->codec);
        if (!h264->codec_ctx) {
            std::cerr << "Failed to allocate H.264 codec context" << std::endl;
            delete h264;
            return;
        }
        
        if (avcodec_open2(h264->codec_ctx, h264->codec, NULL) < 0) {
            std::cerr << "Failed to open H.264 codec" << std::endl;
            avcodec_free_context(&h264->codec_ctx);
            delete h264;
            return;
        }
        
        h264->frame = av_frame_alloc();
        h264->packet = av_packet_alloc();
        
        if (!h264->frame || !h264->packet) {
            std::cerr << "Failed to allocate H.264 frame/packet" << std::endl;
            if (h264->frame) av_frame_free(&h264->frame);
            if (h264->packet) av_packet_free(&h264->packet);
            avcodec_free_context(&h264->codec_ctx);
            delete h264;
            return;
        }
        
        h264->initialized = true;
        h264_decoder_ = h264;
    }
    
    std::vector<uint8_t> decodeVP9Tile(const std::vector<uint8_t>& encoded_data) {
        if (!vp9_decoder_) return {};
        
        VP9Decoder* decoder = static_cast<VP9Decoder*>(vp9_decoder_);
        vpx_codec_iter_t iter = NULL;
        vpx_image_t* img = NULL;
        
        if (vpx_codec_decode(&decoder->codec, encoded_data.data(), encoded_data.size(), NULL, 0)) {
            std::cerr << "VP9 decode failed" << std::endl;
            return {};
        }
        
        img = vpx_codec_get_frame(&decoder->codec, &iter);
        if (!img) {
            return {};
        }
        
        // Convert YUV to RGBA
        std::vector<uint8_t> rgba_data(img->d_w * img->d_h * 4);
        ConvertI420ToRGBA(img, rgba_data.data(), img->d_w, img->d_h);
        
        return rgba_data;
    }
    
    std::vector<uint8_t> decodeH264Tile(const std::vector<uint8_t>& encoded_data) {
        if (!h264_decoder_) return {};
        
        H264Decoder* decoder = static_cast<H264Decoder*>(h264_decoder_);
        
        decoder->packet->data = const_cast<uint8_t*>(encoded_data.data());
        decoder->packet->size = encoded_data.size();
        
        int ret = avcodec_send_packet(decoder->codec_ctx, decoder->packet);
        if (ret < 0) {
            std::cerr << "Error sending H.264 packet" << std::endl;
            return {};
        }
        
        ret = avcodec_receive_frame(decoder->codec_ctx, decoder->frame);
        if (ret < 0) {
            if (ret != AVERROR(EAGAIN)) {
                std::cerr << "Error receiving H.264 frame" << std::endl;
            }
            return {};
        }
        
        // Convert to RGBA
        int width = decoder->frame->width;
        int height = decoder->frame->height;
        std::vector<uint8_t> rgba_data(width * height * 4);
        
        if (!decoder->sws_ctx) {
            decoder->sws_ctx = sws_getContext(
                width, height, static_cast<AVPixelFormat>(decoder->frame->format),
                width, height, AV_PIX_FMT_RGBA,
                SWS_BILINEAR, NULL, NULL, NULL);
        }
        
        if (decoder->sws_ctx) {
            uint8_t* dst_data[4] = { rgba_data.data(), NULL, NULL, NULL };
            int dst_linesize[4] = { width * 4, 0, 0, 0 };
            
            sws_scale(decoder->sws_ctx, decoder->frame->data, decoder->frame->linesize,
                     0, height, dst_data, dst_linesize);
        }
        
        return rgba_data;
    }
    
    void ConvertI420ToRGBA(vpx_image_t* img, uint8_t* rgba_data, int width, int height) {
        uint8_t* y_plane = img->planes[VPX_PLANE_Y];
        uint8_t* u_plane = img->planes[VPX_PLANE_U];
        uint8_t* v_plane = img->planes[VPX_PLANE_V];
        
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int y_idx = y * img->stride[VPX_PLANE_Y] + x;
                int uv_idx = (y / 2) * img->stride[VPX_PLANE_U] + (x / 2);
                
                uint8_t Y = y_plane[y_idx];
                uint8_t U = u_plane[uv_idx];
                uint8_t V = v_plane[uv_idx];
                
                // YUV to RGB conversion
                int C = Y - 16;
                int D = U - 128;
                int E = V - 128;
                
                int R = (298 * C + 409 * E + 128) >> 8;
                int G = (298 * C - 100 * D - 208 * E + 128) >> 8;
                int B = (298 * C + 516 * D + 128) >> 8;
                
                int rgba_idx = (y * width + x) * 4;
                rgba_data[rgba_idx + 0] = std::clamp(R, 0, 255);
                rgba_data[rgba_idx + 1] = std::clamp(G, 0, 255);
                rgba_data[rgba_idx + 2] = std::clamp(B, 0, 255);
                rgba_data[rgba_idx + 3] = 255; // Alpha
            }
        }
    }
    
    void* vp9_decoder_ = nullptr;
    void* h264_decoder_ = nullptr;
};

// Export C++ functions to JavaScript
EMSCRIPTEN_BINDINGS(wasm_decoder) {
    emscripten::class_<WasmTileDecoder>("WasmTileDecoder")
        .constructor<>()
        .function("decodeTiles", &WasmTileDecoder::decodeTiles);
        
    emscripten::register_vector<uint8_t>("vector<uint8_t>");
}

// C-style exports for direct calling
extern "C" {
    EMSCRIPTEN_KEEPALIVE
    WasmTileDecoder* create_decoder() {
        return new WasmTileDecoder();
    }
    
    EMSCRIPTEN_KEEPALIVE
    void destroy_decoder_instance(WasmTileDecoder* decoder) {
        delete decoder;
    }
    
    EMSCRIPTEN_KEEPALIVE
    int decode_tile_direct(WasmTileDecoder* decoder, 
                          uint8_t* encoded_data, int encoded_size,
                          int codec_type,
                          uint8_t* output_buffer) {
        std::vector<uint8_t> input(encoded_data, encoded_data + encoded_size);
        auto result = decoder->decodeTile(input, codec_type);
        
        if (!result.empty()) {
            std::memcpy(output_buffer, result.data(), result.size());
            return result.size();
        }
        
        return 0;
    }
}