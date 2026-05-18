// Array of structs, where each element itself contains an array of structs.
// Exercises pos-advance through two layers of struct-array iteration plus a
// trailing primitive — regression check for the from_struct slicing path.

typedef struct Cell {
    int16_t a;
    int16_t b;
};

typedef struct Row {
    Cell     cells[3];
    uint32_t tag;
};

typedef struct Grid {
    Row     rows[2];
    uint8_t marker;
};
