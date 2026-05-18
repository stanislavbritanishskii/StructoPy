// Multi-token C primitive types. Earlier versions of the parser only inspected
// the first whitespace-separated token, so `unsigned int x;` reported the type
// as `unsigned` and bailed out. This fixture pins the longest-match behaviour.

typedef struct MultiToken {
    signed char        sc;
    unsigned char      uc;
    unsigned short     us;
    unsigned int       ui;
    unsigned long      ul;
    long long          ll;
    unsigned long long ull;
    short              s;
    long               l;
};
