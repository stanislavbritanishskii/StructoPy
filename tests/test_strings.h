// Char arrays at various sizes plus a single char in front of an integer
// to confirm pos advances correctly after a single char field.

typedef struct Strings {
    char     short_str[8];
    char     medium_str[32];
    char     long_str[128];
    char     single_char;
    uint32_t after_single;
    char     trailing[16];
};
