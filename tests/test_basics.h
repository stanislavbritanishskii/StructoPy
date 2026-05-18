// Every primitive type StructoPy claims to support, plus a wide-field telemetry record.

typedef struct AllPrimitives {
    uint8_t  u8;
    int8_t   i8;
    uint16_t u16;
    int16_t  i16;
    uint32_t u32;
    int32_t  i32;
    uint64_t u64;
    int64_t  i64;
    float    f;
    double   d;
    char     c;
    bool     b;
};

typedef struct WideRecord {
    uint32_t id;
    uint32_t version;
    int64_t  timestamp_ns;
    float    voltage;
    float    current;
    float    temperature;
    uint16_t status;
    uint8_t  error_code;
    uint8_t  reserved;
};
