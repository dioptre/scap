/**
 * Simple protobuf decoder for frame data.
 * Decodes binary protobuf messages from the WebSocket.
 */

class ProtobufDecoder {
    constructor() {
        // Field numbers from frame_data.proto
        this.FRAME_FIELDS = {
            FRAME_ID: 1,
            WIDTH: 2, 
            HEIGHT: 3,
            URL: 4,
            TILES: 5,
            TILE_COUNT: 6,
            TIMESTAMP: 7
        };
        
        this.TILE_FIELDS = {
            TILE_ID: 1,
            X: 2,
            Y: 3,
            WIDTH: 4,
            HEIGHT: 5,
            CODEC: 6,
            HAS_MOTION: 7,
            DATA: 8,
            SIZE: 9,
            TIMESTAMP: 10
        };
    }
    
    decodeFrame(buffer) {
        const view = new DataView(buffer);
        let offset = 0;
        const frame = {};
        const tiles = [];
        
        while (offset < buffer.byteLength) {
            const { field, wireType, value, newOffset } = this.decodeField(view, offset);
            offset = newOffset;
            
            switch (field) {
                case this.FRAME_FIELDS.FRAME_ID:
                    frame.frame_id = value;
                    break;
                case this.FRAME_FIELDS.WIDTH:
                    frame.width = value;
                    break;
                case this.FRAME_FIELDS.HEIGHT:
                    frame.height = value;
                    break;
                case this.FRAME_FIELDS.URL:
                    frame.url = this.decodeString(view, value, offset - value);
                    break;
                case this.FRAME_FIELDS.TILES:
                    const tile = this.decodeTile(view, value, offset - value);
                    tiles.push(tile);
                    break;
                case this.FRAME_FIELDS.TILE_COUNT:
                    frame.tile_count = value;
                    break;
                case this.FRAME_FIELDS.TIMESTAMP:
                    frame.timestamp = value;
                    break;
            }
        }
        
        frame.tiles = tiles;
        return frame;
    }
    
    decodeTile(view, length, offset) {
        const tile = {};
        const endOffset = offset + length;
        
        while (offset < endOffset) {
            const { field, wireType, value, newOffset } = this.decodeField(view, offset);
            offset = newOffset;
            
            switch (field) {
                case this.TILE_FIELDS.TILE_ID:
                    tile.tile_id = this.decodeString(view, value, offset - value);
                    break;
                case this.TILE_FIELDS.X:
                    tile.x = value;
                    break;
                case this.TILE_FIELDS.Y:
                    tile.y = value;
                    break;
                case this.TILE_FIELDS.WIDTH:
                    tile.width = value;
                    break;
                case this.TILE_FIELDS.HEIGHT:
                    tile.height = value;
                    break;
                case this.TILE_FIELDS.CODEC:
                    tile.codec = this.decodeString(view, value, offset - value);
                    break;
                case this.TILE_FIELDS.HAS_MOTION:
                    tile.has_motion = value !== 0;
                    break;
                case this.TILE_FIELDS.DATA:
                    tile.data = new Uint8Array(view.buffer, offset - value, value);
                    break;
                case this.TILE_FIELDS.SIZE:
                    tile.size = value;
                    break;
                case this.TILE_FIELDS.TIMESTAMP:
                    tile.timestamp = value;
                    break;
            }
        }
        
        return tile;
    }
    
    decodeField(view, offset) {
        const varint = this.decodeVarint(view, offset);
        const tag = varint.value;
        const field = tag >>> 3;
        const wireType = tag & 0x7;
        
        offset = varint.offset;
        
        switch (wireType) {
            case 0: // Varint
                const varintValue = this.decodeVarint(view, offset);
                return {
                    field,
                    wireType,
                    value: varintValue.value,
                    newOffset: varintValue.offset
                };
                
            case 2: // Length-delimited
                const length = this.decodeVarint(view, offset);
                return {
                    field,
                    wireType,
                    value: length.value,
                    newOffset: length.offset + length.value
                };
                
            default:
                throw new Error(`Unsupported wire type: ${wireType}`);
        }
    }
    
    decodeVarint(view, offset) {
        let value = 0;
        let shift = 0;
        
        while (offset < view.byteLength) {
            const byte = view.getUint8(offset++);
            value |= (byte & 0x7F) << shift;
            
            if ((byte & 0x80) === 0) {
                break;
            }
            
            shift += 7;
        }
        
        return { value, offset };
    }
    
    decodeString(view, length, offset) {
        const bytes = new Uint8Array(view.buffer, offset, length);
        return new TextDecoder().decode(bytes);
    }
}