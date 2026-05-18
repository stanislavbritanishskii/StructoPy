// `typedef struct { ... } Name;` — name only appears AFTER the body.
// Pre-fix this generated `class :` (syntax error in the output module).

typedef struct {
    int32_t  a;
    float    b;
    uint16_t c;
    uint8_t  d;
} AnonOnly;

typedef struct {
    AnonOnly first;
    AnonOnly second;
    int64_t  marker;
} AnonNestedUser;
