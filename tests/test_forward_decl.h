// Regression: a forward declaration like `struct Foo;` must not steal the body
// of the next struct. Before the fix the parser would pick up the name `Early`
// from the forward decl, then scan forward to the next `{` — landing in
// `Later`'s body and emitting one class named `Early` with `Later`'s fields,
// while `Later` itself was never generated.

struct Early;

typedef struct Later {
    int32_t value;
    int32_t tag;
};
