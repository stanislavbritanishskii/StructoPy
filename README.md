# StructoPy

StructoPy is a lightweight code generator that converts C/C++ struct definitions into Python classes for binary-safe data exchange.

It is designed for simple, deterministic serialization between C++ and Python — UDP traffic, embedded systems (ESP32, Cortex-M), robotics data pipelines, and any other place you want low-overhead binary IPC without dragging in a schema framework.

---

## Quick start

```bash
./run.sh sample.h
```

This will:

1. Preprocess the input header (resolving user `""`-form `#include`s, stubbing system `<>`-form ones)
2. Parse every struct definition
3. Write Python classes to `/tmp/structopy/output.py`
4. Auto-generate `/tmp/structopy/test.py`, which instantiates each class and prints its size and format string

All generated artifacts (`output.py`, `temp.hpp`, `test.py`) live under `/tmp/structopy/` so the repo working tree stays clean. Re-running overwrites them in place.

To pass additional include search paths to the preprocessor:

```bash
./run.sh -I src/inc -I vendor/inc input.h
```

### Endianness

The serialized byte order defaults to little-endian. Select big-endian at generation time with `--endian`:

```bash
./run.sh --endian big sample.h           # network / big-endian payloads
./run.sh --endian little sample.h        # explicit (default)
```

The same flag works on `main.py` directly:

```bash
python3 main.py --endian big input.h > output.py
```

The choice is baked into the generated module — every generated class' `to_struct` / `from_struct` uses the selected byte order. Mix only generators built with the same `--endian` value on both ends of a wire.

---

## Generated API

Every generated class exposes:

| Method | Purpose |
|---|---|
| `to_struct()` | Serialize the object into `bytes` |
| `from_struct(binary)` | Deserialize `bytes` back into the object |
| `get_size()` | Total byte size of the struct |
| `get_format_string()` | The Python `struct` format string used for packing |

Example:

```python
# Either copy /tmp/structopy/output.py into your project, or:
import sys; sys.path.insert(0, "/tmp/structopy")
from output import Sensor

s = Sensor()
s.id = 7
s.value = 4.5
buf = s.to_struct()       # bytes — ready for UDP / disk / pipe

s2 = Sensor()
s2.from_struct(buf)
assert s2.id == 7
```

---

## Requirements

* Python 3.x
* `gcc` in `$PATH` (used for preprocessing and dependency discovery)

```bash
gcc --version
```

---

## Supported C/C++ syntax

### Struct declarations

All four common forms are accepted:

```c
struct Name { ... };                  // C/C++ tagged form
typedef struct Name { ... };          // typedef with tag
typedef struct Name { ... } Alias;    // typedef with separate alias
typedef struct { ... } Name;          // anonymous typedef (name appears after the body)
```

The tag name (or the trailing alias, for anonymous typedefs) becomes the Python class name.

### Attributes

`__attribute__((...))` is recognized in any position and **stripped** before parsing. StructoPy already emits packed binary layout (no padding), so the attribute is effectively a no-op:

```c
typedef struct __attribute__((packed)) { ... } Foo;
typedef struct __attribute__((packed, aligned(1))) Bar { ... };
typedef struct { ... } __attribute__((packed)) Baz;
struct __attribute__((packed)) Qux { ... };
```

### Types

* All basic C types: `int`, `char`, `float`, `double`, `bool`, `short`, `long`, `long long`
* Fixed-width: `int8_t` / `uint8_t` / … / `int64_t` / `uint64_t`
* Fixed-size arrays: `int values[10];`
* Nested structs (recursive, any depth)
* Structs imported from `#include "..."` user headers

### Includes

`run.sh` uses `gcc -M -MG -nostdinc` to discover the full transitive include tree, then classifies each header:

* **User headers** (resolvable on disk under the input directory or any `-I` path) are preprocessed normally. Subdirectories work.
* **System headers** (`<vector>`, `<string>`, `<stdint.h>`, …) are detected as "missing" and replaced with empty stub files. A one-line summary is printed:

  ```
  Stubbed 2 system header(s): stdint.h vector
  ```

This means you can `#include <stdint.h>` for `uint32_t` etc. without StructoPy choking on the actual C++ standard library.

---

## What StructoPy rejects

The generator **errors out with a clear message** rather than producing broken output for:

| Input | Why rejected |
|---|---|
| `void* ptr;` (any pointer) | Pointer values don't survive serialization. Use `uint32_t` / `uint64_t` if you need to round-trip an opaque handle. |
| `unsigned int flag : 4;` (bit fields) | C bit-field layout is implementation-defined. Pack bits manually into a plain integer and shift/mask. |
| `MyCustomType x;` (unknown type) | Error lists every known primitive and previously-declared struct so you can spot the typo. |
| Truncated input (missing `}`) | Reports "unmatched '{'" instead of an `IndexError`. |

---

## Limitations

The following are not supported (and will surface as "unknown type" errors if you use them):

* `std::vector`, `std::string`, other STL types
* Function pointers, member functions, virtual methods
* C++ inheritance, templates, namespaces
* Anonymous unions and nested struct *definitions* inside another struct

Endianness is fixed at generation time (default little-endian). Pass `--endian big` to `run.sh` / `main.py` to switch — see [Endianness](#endianness) above. There is no per-call runtime switch on the generated classes.

---

## Testing

```bash
python3 tests/run_tests.py
```

The harness covers:

* All primitive types in encode→decode→equality round trips
* Multi-level nested structs (three levels deep)
* Arrays of primitives, arrays of structs, mixed
* Strings at boundary sizes (empty, mid-length, exactly array-size, embedded NULs)
* Anonymous typedefs, with and without `__attribute__((packed))`
* Full `run.sh` preprocessing pipeline with subdir user includes plus stubbed system includes
* Every rejected-input case (pointer / bit field / unknown type / truncated)

Each subprocess runs under a 10-second timeout so a bad input can never wedge the harness.

---

## Design philosophy

StructoPy is intentionally minimal:

* No schema language
* No runtime dependencies — the generated module only needs `struct` and `ctypes` from the stdlib
* No external serialization frameworks
* Direct mapping: C struct → Python binary class, same bytes on both sides by construction

If you need versioning, schema evolution, or self-describing payloads, use protobuf or msgpack. If you control both ends and just want to move structs around, this is the tool.

---

## Project layout

```
StructoPy/
├── main.py             # generator
├── run.sh              # preprocess → generate → smoke-test driver
├── sample.h            # demo input
├── included_sample.h   # demo user include
└── tests/
    ├── run_tests.py    # test harness (92 checks)
    ├── test_*.h        # good headers
    ├── bad_*.h         # rejected-input fixtures
    └── test_includes/  # multi-file user-include layout
```

---

## Author

Stanislav Britanishskii — <https://github.com/stanislavbritanishskii/StructoPy>

## License

MIT — see `LICENSE`.
