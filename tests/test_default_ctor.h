// Regression: C++ struct member functions (constructors, destructors, member
// functions, default/delete forms) must not break field parsing. Earlier
// versions errored out on the ':' in a member initializer list (treating it
// as a bit field) or on the '(' (treating the line as an unknown type).

typedef struct WithCtor {
    WithCtor() : a(0), b(0) {}
    WithCtor(int32_t initial_a) : a(initial_a), b(0) {}
    ~WithCtor() {}

    int32_t a;
    int32_t b;
};

struct WithMethods {
    int32_t x;
    int32_t y;

    int32_t sum() const {
        int32_t result = x + y;
        return result;
    }

    void reset() {
        x = 0;
        y = 0;
    }
};

struct WithDefaultDelete {
    WithDefaultDelete() = default;
    WithDefaultDelete(const WithDefaultDelete&) = delete;
    int32_t value;
};

struct WithAccessSpec {
public:
    int32_t pub_val;
private:
    int32_t priv_val;
};
