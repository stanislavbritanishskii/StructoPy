// Arrays of primitives, arrays of structs, and a mixed combo.

typedef struct PointI {
    int32_t x;
    int32_t y;
};

typedef struct ArrayCombo {
    uint8_t  buffer[256];
    uint32_t indices[16];
    PointI   points[8];
    double   matrix[9];
    int16_t  signed_arr[4];
    uint16_t count;
};
