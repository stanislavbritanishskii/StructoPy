# StructoPy

StructoPy is a lightweight code generator that converts C/C++ struct definitions into Python classes for binary-safe data exchange.

It is designed for simple, deterministic serialization between C++ and Python, primarily for use cases such as:
- UDP-based communication
- embedded systems (e.g. ESP32)
- robotics data pipelines
- low-overhead IPC between C++ and Python

---

## Features

StructoPy generates Python classes directly from C/C++ struct definitions found in `.hpp` or `.h` files.

Each generated class includes:

- `to_struct()`  
  Serialize the object into a binary representation

- `from_struct(bytes)`  
  Deserialize binary data back into the object

- `get_size()`  
  Returns total byte size of the struct

- `get_format_string(secondary_call=False)`  
  Generates a Python `struct` format string for packing/unpacking

> Note: `secondary_call` is used internally when generating nested structures to avoid recursion depth issues.

---

## Usage

Run StructoPy with:

```bash id="cli1"
./run.sh file.hpp
```

This will:

1. Parse the input header file
2. Generate Python classes
3. Create a basic automatic test file
4. Execute simple validation tests that print results to stdout

---

## Requirements

StructoPy requires:

* Python 3.x
* g++ compiler (used for preprocessing and macro expansion of C/C++ headers)

Make sure `g++` is available in your system PATH:

```bash id="req1"
g++ --version
```

---

## Supported C/C++ Syntax

StructoPy currently supports only explicit struct definitions:

### Required formats:

```cpp id="cpp3"
struct Name {
	int a;
	float b;
};
```

or

```cpp id="cpp4"
typedef struct Name {
	int a;
	float b;
} Name;
```

The struct name is used as the Python class name.

---

## Supported Types

StructoPy supports:

* All basic C types (`int`, `char`, `float`, `double`, etc.)
* Fixed-size arrays:

  ```cpp id="cpp5"
  int values[10];
  ```
* Nested structs (recursive support)
* Struct composition across included project headers

---

## Limitations

StructoPy is intentionally minimal and does NOT support:

* `std::vector`, `std::string`, or STL containers
* functions inside structs
* dynamic memory structures
* complex C++ class features
* automatic endian conversion (always little-endian: `<`)

---

## Includes

StructoPy can resolve user-defined includes between project headers.

However:

* It does NOT reliably handle large standard library headers
* Includes such as `<vector>`, `<string>`, etc. are ignored or may fail

---

## Endianness

All serialization is currently fixed to:

```text id="end1"
Little Endian (`<`)
```

No runtime or per-field endianness switching is implemented.

---

## Design Philosophy

StructoPy is intentionally simple:

* no schema language
* no runtime dependencies
* no external serialization frameworks
* direct mapping from C struct → Python binary class

The goal is predictable binary communication with minimal overhead.

---

## Example Workflow

```bash id="ex1"
./run.sh sample.h
```

Output:

* Generated Python classes
* Auto-generated test file
* Printed test results validating serialization correctness

---

## Author

Stanislav Britanishskii
[https://github.com/stanislavbritanishskii/StructoPy](https://github.com/stanislavbritanishskii/StructoPy)

---

## License

This project is licensed under the MIT License.

See the LICENSE file for details.

