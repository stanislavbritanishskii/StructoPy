// Every common placement of __attribute__ that real-world C code uses.
// StructoPy already emits packed layout, so these should all parse the same.

// 1) Anonymous typedef + attribute between `struct` and `{`
//    (the combination the user specifically asked about)
typedef struct __attribute__((packed)) {
    uint8_t  flag;
    uint32_t value;
    uint16_t tail;
} PackedAnon;

// 2) Named struct with multiple attributes (multi-arg list)
typedef struct __attribute__((packed, aligned(1))) Named {
    uint8_t  a;
    uint32_t b;
    uint8_t  c;
};

// 3) Attribute between `}` and the trailing typedef name
typedef struct {
    uint16_t x;
    uint16_t y;
} __attribute__((packed)) PostAttr;

// 4) Plain `struct Name` (no typedef) with attribute
struct __attribute__((packed)) NoTypedef {
    int32_t z;
    int32_t w;
};

// 5) Nested attribute paren — should not confuse the stripper
typedef struct __attribute__((aligned(__alignof__(int)))) Inner {
    uint8_t k;
    uint8_t v;
};
