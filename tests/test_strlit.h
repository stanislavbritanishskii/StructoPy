// Code-level string and char literals that contain the word `struct` must not
// fool the struct scanner. Earlier versions would treat the contents of the
// literal as a struct body and emit a phantom class.

typedef struct Real {
    int32_t a;
    int32_t b;
};

const char *msg = "struct GhostString { fake } end";
const char  c   = 's';
const char *msg2 = "another struct GhostString2 { also fake }";
