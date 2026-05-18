// `typedef struct Tag { ... } Alias;` — both names must be usable.
// Earlier versions only kept the tag and the alias was reported as an unknown
// type when another struct referenced it.

typedef struct PairTag {
    int32_t a;
    int32_t b;
} PairAlias;

// Reference via the alias
typedef struct UsesAlias {
    PairAlias pa;
    int32_t   tail;
};

// Reference via the original tag
typedef struct UsesTag {
    PairTag   pt;
    int32_t   tail;
};
