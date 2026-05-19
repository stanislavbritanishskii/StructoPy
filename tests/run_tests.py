"""StructoPy test harness.

Runs main.py against every test header in tests/, then:
  - for *good* headers: imports the generated module and runs round-trip checks
  - for *bad* headers: asserts main.py exits non-zero with the expected error keyword

Hard timeout on every subprocess so a hang in main.py can't wedge the harness.
"""
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAIN = os.path.join(ROOT, "main.py")
SUBPROCESS_TIMEOUT = 10  # seconds

PASS = 0
FAIL = 0

def report(label, ok, info=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}{(' — ' + info) if info else ''}")

def generate(header_path, extra_args=()):
    """Run main.py on a header. Returns (rc, stdout, stderr)."""
    try:
        r = subprocess.run(
            [sys.executable, MAIN, *extra_args, header_path],
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {SUBPROCESS_TIMEOUT}s"

def load_generated(code, modname):
    mod = types.ModuleType(modname)
    exec(code, mod.__dict__)
    return mod

# ----------------------------------------------------------------------------
# Good headers — must generate AND round-trip
# ----------------------------------------------------------------------------

def test_basics():
    print("\n=== test_basics ===")
    rc, out, err = generate(os.path.join(HERE, "test_basics.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_basics")

    # AllPrimitives — load every field with a distinct sentinel
    a = m.AllPrimitives()
    a.u8 = 200
    a.i8 = -100
    a.u16 = 60000
    a.i16 = -30000
    a.u32 = 4000000000
    a.i32 = -2000000000
    a.u64 = 18000000000000000000
    a.i64 = -9000000000000000000
    a.f = 1.25
    a.d = 3.141592653589793
    a.c = "Z"
    a.b = True
    b = a.to_struct()
    a2 = m.AllPrimitives(); a2.from_struct(b)
    for fld in ("u8","i8","u16","i16","u32","i32","u64","i64","c","b"):
        report(f"AllPrimitives.{fld}", getattr(a2, fld) == getattr(a, fld),
               f"got {getattr(a2, fld)!r} expected {getattr(a, fld)!r}")
    report("AllPrimitives.f", abs(a2.f - a.f) < 1e-6, f"got {a2.f}")
    report("AllPrimitives.d", abs(a2.d - a.d) < 1e-12, f"got {a2.d}")
    report("AllPrimitives size matches calcsize",
           a.get_size() == len(b), f"declared {a.get_size()}, actual {len(b)}")

    # WideRecord
    w = m.WideRecord()
    w.id = 42
    w.version = 7
    w.timestamp_ns = -1234567890123
    w.voltage = 24.0
    w.current = 3.5
    w.temperature = 36.6
    w.status = 0x1234
    w.error_code = 0
    w.reserved = 0
    b = w.to_struct()
    w2 = m.WideRecord(); w2.from_struct(b)
    for fld in ("id","version","timestamp_ns","status","error_code","reserved"):
        report(f"WideRecord.{fld}", getattr(w2, fld) == getattr(w, fld))
    for fld in ("voltage","current","temperature"):
        report(f"WideRecord.{fld}", abs(getattr(w2, fld) - getattr(w, fld)) < 1e-4)


def test_nested():
    print("\n=== test_nested ===")
    rc, out, err = generate(os.path.join(HERE, "test_nested.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_nested")

    rs = m.RobotState()
    rs.base_pose.position.x = 1.0
    rs.base_pose.position.y = 2.0
    rs.base_pose.position.z = 3.0
    rs.base_pose.orientation.w = 1.0
    rs.base_pose.orientation.x = 0.0
    rs.base_pose.orientation.y = 0.0
    rs.base_pose.orientation.z = 0.0
    rs.tool_pose.position.x = -1.5
    rs.tool_pose.position.y = -2.5
    rs.tool_pose.position.z = -3.5
    rs.tool_pose.orientation.w = 0.5
    rs.tool_pose.orientation.x = 0.5
    rs.tool_pose.orientation.y = 0.5
    rs.tool_pose.orientation.z = 0.5
    rs.timestamp_ns = 1700000000000000000
    rs.sequence = 0xCAFEBABE
    rs.mode = 3
    rs.battery_percent = 87
    b = rs.to_struct()

    rs2 = m.RobotState(); rs2.from_struct(b)
    report("base_pose.position.x", rs2.base_pose.position.x == 1.0)
    report("base_pose.position.z", rs2.base_pose.position.z == 3.0)
    report("base_pose.orientation.w", rs2.base_pose.orientation.w == 1.0)
    report("tool_pose.position.y", rs2.tool_pose.position.y == -2.5)
    report("tool_pose.orientation.z", rs2.tool_pose.orientation.z == 0.5)
    report("timestamp_ns", rs2.timestamp_ns == 1700000000000000000,
           f"got {rs2.timestamp_ns}")
    report("sequence", rs2.sequence == 0xCAFEBABE, f"got {hex(rs2.sequence)}")
    report("mode", rs2.mode == 3)
    report("battery_percent", rs2.battery_percent == 87)


def test_arrays():
    print("\n=== test_arrays ===")
    rc, out, err = generate(os.path.join(HERE, "test_arrays.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_arrays")

    a = m.ArrayCombo()
    a.buffer = [i % 256 for i in range(256)]
    a.indices = [i * 1000 for i in range(16)]
    for i in range(8):
        a.points[i].x = i * 10
        a.points[i].y = i * 10 + 1
    a.matrix = [float(i) * 1.5 for i in range(9)]
    a.signed_arr = [-1, -2, -3, -4]
    a.count = 8
    b = a.to_struct()

    a2 = m.ArrayCombo(); a2.from_struct(b)
    report("buffer[0]", a2.buffer[0] == 0)
    report("buffer[255]", a2.buffer[255] == 255)
    report("indices[7]", a2.indices[7] == 7000)
    report("points[5].x", a2.points[5].x == 50)
    report("points[5].y", a2.points[5].y == 51)
    report("points[7].y", a2.points[7].y == 71)
    report("matrix[4]", abs(a2.matrix[4] - 6.0) < 1e-6, f"got {a2.matrix[4]}")
    report("signed_arr[2]", a2.signed_arr[2] == -3)
    report("count", a2.count == 8)


def test_strings():
    print("\n=== test_strings ===")
    rc, out, err = generate(os.path.join(HERE, "test_strings.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_strings")

    s = m.Strings()
    s.short_str = "hi"            # under length
    s.medium_str = "M" * 32       # exactly length, no null room
    s.long_str = "long-payload-text"
    s.single_char = "X"
    s.after_single = 0xDEADBEEF   # critical: catches pos-advance bug regression
    s.trailing = "tail"
    b = s.to_struct()

    s2 = m.Strings(); s2.from_struct(b)
    report("short_str strict eq", s2.short_str == "hi", f"got {s2.short_str!r}")
    report("medium_str exactly-32 strict eq", s2.medium_str == "M" * 32,
           f"got {s2.medium_str!r}")
    report("long_str strict eq", s2.long_str == "long-payload-text",
           f"got {s2.long_str!r}")
    report("single_char strict eq", s2.single_char == "X", f"got {s2.single_char!r}")
    report("after_single (regression check for pos-advance bug)",
           s2.after_single == 0xDEADBEEF,
           f"got {hex(s2.after_single) if isinstance(s2.after_single,int) else s2.after_single!r}")
    report("trailing strict eq", s2.trailing == "tail", f"got {s2.trailing!r}")


def test_anonymous():
    print("\n=== test_anonymous ===")
    rc, out, err = generate(os.path.join(HERE, "test_anonymous.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    # Was producing `class :` before the fix — make sure it's gone.
    report("no empty `class :` in generated output", "class :" not in out,
           "anonymous typedef name was not recovered")
    m = load_generated(out, "gen_anonymous")

    a = m.AnonOnly()
    a.a = -12345
    a.b = 2.5
    a.c = 60000
    a.d = 7
    b = a.to_struct()
    a2 = m.AnonOnly(); a2.from_struct(b)
    report("AnonOnly.a", a2.a == a.a)
    report("AnonOnly.b", abs(a2.b - a.b) < 1e-6)
    report("AnonOnly.c", a2.c == a.c)
    report("AnonOnly.d", a2.d == a.d)

    # Anonymous struct used as a field type inside another anonymous typedef
    n = m.AnonNestedUser()
    n.first.a = 1; n.first.b = 1.5; n.first.c = 100; n.first.d = 9
    n.second.a = 2; n.second.b = 2.5; n.second.c = 200; n.second.d = 8
    n.marker = -1
    b = n.to_struct()
    n2 = m.AnonNestedUser(); n2.from_struct(b)
    report("AnonNestedUser.first.a", n2.first.a == 1)
    report("AnonNestedUser.second.c", n2.second.c == 200)
    report("AnonNestedUser.marker", n2.marker == -1)


def test_multitoken():
    print("\n=== test_multitoken ===")
    rc, out, err = generate(os.path.join(HERE, "test_multitoken.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_multitoken")

    x = m.MultiToken()
    x.sc = -42
    x.uc = 200
    x.us = 60000
    x.ui = 4000000000
    x.ul = 4000000000
    x.ll = -9000000000000000000
    x.ull = 18000000000000000000
    x.s  = -30000
    x.l  = -2000000000
    b = x.to_struct()

    x2 = m.MultiToken(); x2.from_struct(b)
    for fld in ("sc","uc","us","ui","ul","ll","ull","s","l"):
        report(f"MultiToken.{fld}", getattr(x2, fld) == getattr(x, fld),
               f"got {getattr(x2, fld)!r} expected {getattr(x, fld)!r}")
    report("MultiToken format string contains expected codes",
           # signed char b, unsigned char B, unsigned short H, unsigned int I,
           # unsigned long L, long long q, unsigned long long Q, short h, long l.
           x.get_format_string().endswith("bBHILqQhl"),
           f"got {x.get_format_string()!r}")

    # Regression check: `long` and `unsigned long` use STANDARD (4-byte) sizes,
    # not the native LP64 8-byte sizes. Earlier versions emitted `struct.pack("L", ...)`
    # without an endian prefix, so on Linux pack wrote 8 bytes while the cached
    # format string declared 4 — corrupting every round trip that contained a
    # `long` or `unsigned long`.
    report("serialized length matches format calcsize",
           len(b) == x.get_size(),
           f"len(b)={len(b)} get_size()={x.get_size()}")
    # 1+1+2+4+4+8+8+2+4 = 34 bytes for the field set above
    report("MultiToken declares standard sizes (34 bytes)",
           x.get_size() == 34, f"got {x.get_size()}")


def test_endian_flag():
    """`--endian big|little` must change the byte order of the generated module."""
    print("\n=== test_endian_flag ===")
    header = os.path.join(HERE, "test_multitoken.h")

    # Bad value rejected
    rc, _, err = generate(header, extra_args=("--endian", "middle"))
    report("--endian rejects unknown value", rc != 0 and "endian" in err.lower(),
           f"rc={rc} err={err.strip()[:200]}")

    # Big-endian generation
    rc, out_be, err = generate(header, extra_args=("--endian", "big"))
    report("--endian big exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m_be = load_generated(out_be, "gen_be")
    x = m_be.MultiToken()
    x.sc = -1; x.uc = 1; x.us = 1; x.ui = 1; x.ul = 1
    x.ll = 1; x.ull = 1; x.s = 1; x.l = 1
    b_be = x.to_struct()
    # ui is uint32_t = 1: in big-endian its 4 bytes are 00 00 00 01.
    # Offset in buffer: sc(1) + uc(1) + us(2) = 4 → ui at bytes [4:8]
    report("--endian big writes BE bytes for uint32_t = 1",
           b_be[4:8] == b'\x00\x00\x00\x01', f"got {b_be[4:8].hex()}")
    x2 = m_be.MultiToken(); x2.from_struct(b_be)
    report("--endian big round-trips", x2.ui == 1 and x2.ull == 1)

    # Little-endian generation (control)
    rc, out_le, err = generate(header, extra_args=("--endian", "little"))
    report("--endian little exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m_le = load_generated(out_le, "gen_le")
    y = m_le.MultiToken()
    y.sc = -1; y.uc = 1; y.us = 1; y.ui = 1; y.ul = 1
    y.ll = 1; y.ull = 1; y.s = 1; y.l = 1
    b_le = y.to_struct()
    report("--endian little writes LE bytes for uint32_t = 1",
           b_le[4:8] == b'\x01\x00\x00\x00', f"got {b_le[4:8].hex()}")

    # Same logical struct, different bytes
    report("BE and LE produce different bytes", b_be != b_le)
    # Same length though — sizes are not endian-sensitive
    report("BE and LE same size", len(b_be) == len(b_le),
           f"be={len(b_be)} le={len(b_le)}")


def test_typedef_alias():
    print("\n=== test_typedef_alias ===")
    rc, out, err = generate(os.path.join(HERE, "test_typedef_alias.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_alias")

    # Reference via the alias
    ua = m.UsesAlias()
    ua.pa.a = 11; ua.pa.b = 22; ua.tail = 7
    b = ua.to_struct()
    ua2 = m.UsesAlias(); ua2.from_struct(b)
    report("UsesAlias.pa.a", ua2.pa.a == 11)
    report("UsesAlias.pa.b", ua2.pa.b == 22)
    report("UsesAlias.tail", ua2.tail == 7)

    # Reference via the original tag (same underlying struct)
    ut = m.UsesTag()
    ut.pt.a = 100; ut.pt.b = 200; ut.tail = 9
    b = ut.to_struct()
    ut2 = m.UsesTag(); ut2.from_struct(b)
    report("UsesTag.pt.a", ut2.pt.a == 100)
    report("UsesTag.pt.b", ut2.pt.b == 200)
    report("UsesTag.tail", ut2.tail == 9)


def test_nested_array():
    print("\n=== test_nested_array ===")
    rc, out, err = generate(os.path.join(HERE, "test_nested_array.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_nested_array")

    g = m.Grid()
    for ri in range(2):
        for ci in range(3):
            g.rows[ri].cells[ci].a = ri * 100 + ci * 10 + 1
            g.rows[ri].cells[ci].b = ri * 100 + ci * 10 + 2
        g.rows[ri].tag = 0xDEAD0000 + ri
    g.marker = 0x7F
    b = g.to_struct()

    # Expected size: rows[2] * (cells[3] * 4 + 4) + 1 = 2 * 16 + 1 = 33
    report("Grid size = 33", g.get_size() == 33, f"got {g.get_size()}")
    report("Grid serialized length matches", len(b) == g.get_size(),
           f"len(b)={len(b)} size={g.get_size()}")

    g2 = m.Grid(); g2.from_struct(b)
    report("rows[0].cells[0].a", g2.rows[0].cells[0].a == 1)
    report("rows[0].cells[2].b", g2.rows[0].cells[2].b == 22)
    report("rows[1].cells[0].a", g2.rows[1].cells[0].a == 101)
    report("rows[1].cells[2].b", g2.rows[1].cells[2].b == 122)
    report("rows[1].tag", g2.rows[1].tag == 0xDEAD0001,
           f"got {hex(g2.rows[1].tag)}")
    report("marker after struct-array", g2.marker == 0x7F,
           f"got {hex(g2.marker)}")


def test_string_literal_keyword():
    """`struct` appearing inside a string/char literal must not be parsed."""
    print("\n=== test_string_literal_keyword ===")
    rc, out, err = generate(os.path.join(HERE, "test_strlit.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    # Real struct must be present, the two ghost names must not.
    report("Real class generated", "class Real" in out)
    report("no phantom GhostString class",
           "class GhostString" not in out,
           "struct keyword inside a string literal was spuriously parsed")
    report("no phantom GhostString2 class",
           "class GhostString2" not in out)

    m = load_generated(out, "gen_strlit")
    r = m.Real(); r.a = 1; r.b = 2
    b = r.to_struct()
    r2 = m.Real(); r2.from_struct(b)
    report("Real.a roundtrip", r2.a == 1)
    report("Real.b roundtrip", r2.b == 2)
    report("module exposes no GhostString attr", not hasattr(m, "GhostString"))


def test_default_ctor():
    """C++ constructors, destructors, member functions and access specifiers
    must be silently skipped — only data fields should be picked up."""
    print("\n=== test_default_ctor ===")
    rc, out, err = generate(os.path.join(HERE, "test_default_ctor.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_default_ctor")

    # WithCtor: constructors + destructor stripped, two int fields remain.
    w = m.WithCtor(); w.a = 11; w.b = 22
    b = w.to_struct()
    w2 = m.WithCtor(); w2.from_struct(b)
    report("WithCtor.a", w2.a == 11)
    report("WithCtor.b", w2.b == 22)
    report("WithCtor size 8", w.get_size() == 8, f"got {w.get_size()}")

    # WithMethods: methods (with multi-line bodies containing assignments)
    # must be stripped, not parsed as fields.
    wm = m.WithMethods(); wm.x = 5; wm.y = 7
    b = wm.to_struct()
    wm2 = m.WithMethods(); wm2.from_struct(b)
    report("WithMethods.x", wm2.x == 5)
    report("WithMethods.y", wm2.y == 7)
    report("WithMethods has only x and y", set(("x", "y")).issubset(wm.__dict__.keys()))
    report("WithMethods has no 'sum' field", "sum" not in wm.__dict__)
    report("WithMethods has no 'result' field", "result" not in wm.__dict__)

    # WithDefaultDelete: `= default` and `= delete` lines skipped, one field.
    wd = m.WithDefaultDelete(); wd.value = 42
    b = wd.to_struct()
    wd2 = m.WithDefaultDelete(); wd2.from_struct(b)
    report("WithDefaultDelete.value", wd2.value == 42)

    # Access specifiers stripped, both fields kept.
    wa = m.WithAccessSpec(); wa.pub_val = 1; wa.priv_val = 2
    b = wa.to_struct()
    wa2 = m.WithAccessSpec(); wa2.from_struct(b)
    report("WithAccessSpec.pub_val", wa2.pub_val == 1)
    report("WithAccessSpec.priv_val", wa2.priv_val == 2)


def test_forward_decl():
    """Forward declaration (`struct Foo;`) must be skipped, not consume the next body."""
    print("\n=== test_forward_decl ===")
    rc, out, err = generate(os.path.join(HERE, "test_forward_decl.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    # The real struct must be `Later`, not `Early`.
    report("Later class generated", "class Later" in out)
    report("no phantom Early class (forward decl skipped)",
           "class Early" not in out,
           "forward declaration was treated as a definition")
    m = load_generated(out, "gen_forward_decl")
    report("module has Later", hasattr(m, "Later"))
    report("module has no Early", not hasattr(m, "Early"))

    l = m.Later(); l.value = 1234; l.tag = 5678
    b = l.to_struct()
    l2 = m.Later(); l2.from_struct(b)
    report("Later.value roundtrip", l2.value == 1234)
    report("Later.tag roundtrip", l2.tag == 5678)


def test_attributes():
    print("\n=== test_attributes ===")
    rc, out, err = generate(os.path.join(HERE, "test_attributes.h"))
    report("generator exits 0", rc == 0, err.strip())
    if rc != 0:
        return
    m = load_generated(out, "gen_attributes")

    # PackedAnon — the anonymous-typedef + __attribute__((packed)) case
    pa = m.PackedAnon()
    pa.flag = 0xAB
    pa.value = 0x12345678
    pa.tail = 0xBEEF
    b = pa.to_struct()
    pa2 = m.PackedAnon(); pa2.from_struct(b)
    report("PackedAnon.flag", pa2.flag == pa.flag)
    report("PackedAnon.value", pa2.value == pa.value, f"got {hex(pa2.value)}")
    report("PackedAnon.tail", pa2.tail == pa.tail)
    report("PackedAnon size (1 + 4 + 2 = 7, no padding)",
           pa.get_size() == 7, f"got {pa.get_size()}")

    # Named (multi-attribute list, named tag)
    n = m.Named()
    n.a = 7; n.b = 0xDEADBEEF; n.c = 9
    b = n.to_struct()
    n2 = m.Named(); n2.from_struct(b)
    report("Named.a", n2.a == 7)
    report("Named.b", n2.b == 0xDEADBEEF, f"got {hex(n2.b)}")
    report("Named.c", n2.c == 9)
    report("Named size (1+4+1=6)", n.get_size() == 6, f"got {n.get_size()}")

    # PostAttr (attribute AFTER the closing brace, before the alias)
    p = m.PostAttr()
    p.x = 100; p.y = 200
    b = p.to_struct()
    p2 = m.PostAttr(); p2.from_struct(b)
    report("PostAttr.x", p2.x == 100)
    report("PostAttr.y", p2.y == 200)

    # NoTypedef (plain `struct Name { ... };`)
    nt = m.NoTypedef()
    nt.z = -999; nt.w = 1234
    b = nt.to_struct()
    nt2 = m.NoTypedef(); nt2.from_struct(b)
    report("NoTypedef.z", nt2.z == -999)
    report("NoTypedef.w", nt2.w == 1234)

    # Inner (nested-paren attribute argument)
    ii = m.Inner()
    ii.k = 5; ii.v = 9
    b = ii.to_struct()
    ii2 = m.Inner(); ii2.from_struct(b)
    report("Inner.k (nested attribute parens stripped correctly)", ii2.k == 5)
    report("Inner.v", ii2.v == 9)


def test_includes():
    """Exercise run.sh: subdir user include is resolved, system include is stubbed."""
    print("\n=== test_includes (run.sh end-to-end) ===")
    import shutil, tempfile

    # Run in an isolated cwd so the generated module lands in workdir, not the
    # repo root. Invoke run.sh straight from the repo — copying it into workdir
    # would put `main.py` (the generator) next to a `main.h` (the input), and
    # the default output filename derivation (`main.h` -> `main.py`) would
    # collide with the generator script.
    workdir = tempfile.mkdtemp()
    try:
        shutil.copytree(os.path.join(HERE, "test_includes"),
                        os.path.join(workdir, "test_includes"))

        try:
            env = os.environ.copy()
            env["STRUCTOPY_ARTIFACT_DIR"] = workdir
            r = subprocess.run(
                ["bash", os.path.join(ROOT, "run.sh"), "test_includes/main.h"],
                cwd=workdir, capture_output=True, text=True,
                timeout=SUBPROCESS_TIMEOUT, env=env,
            )
        except subprocess.TimeoutExpired:
            report("run.sh completes", False, f"TIMEOUT after {SUBPROCESS_TIMEOUT}s")
            return

        report("run.sh exits 0", r.returncode == 0,
               f"stderr: {r.stderr.strip()[:300]}")
        if r.returncode != 0:
            return

        # Expect a "Stubbed N system header(s):" line mentioning stdint.h and vector
        report("reports stubbed system headers",
               "Stubbed" in r.stdout, f"stdout: {r.stdout[:300]}")
        report("stubbed list includes stdint.h",
               "stdint.h" in r.stdout, f"stdout: {r.stdout[:300]}")
        report("stubbed list includes vector",
               "vector" in r.stdout, f"stdout: {r.stdout[:300]}")

        # Default output filename now mirrors the input basename:
        # `test_includes/main.h` -> `main.py` (in cwd = workdir).
        with open(os.path.join(workdir, "main.py"), "r") as f:
            generated = f.read()
        m = load_generated(generated, "gen_includes")

        # Structs from the subdir user header MUST be present
        report("PointF generated from utils/types.h", hasattr(m, "PointF"))
        report("Range generated from utils/types.h",  hasattr(m, "Range"))
        report("Boundary generated from main.h",     hasattr(m, "Boundary"))

        if hasattr(m, "Boundary") and hasattr(m, "PointF") and hasattr(m, "Range"):
            bd = m.Boundary()
            bd.center.x = 1.25
            bd.center.y = -2.5
            bd.span.lo = -100
            bd.span.hi =  100
            bd.flags = 0xCAFEBABE
            b = bd.to_struct()
            bd2 = m.Boundary(); bd2.from_struct(b)
            report("Boundary roundtrip: center.x", bd2.center.x == 1.25)
            report("Boundary roundtrip: span.lo", bd2.span.lo == -100)
            report("Boundary roundtrip: flags",
                   bd2.flags == 0xCAFEBABE, f"got {hex(bd2.flags)}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ----------------------------------------------------------------------------
# Bad headers — must error out, generator should not produce output
# ----------------------------------------------------------------------------

def test_bad(name, header, expected_keyword):
    print(f"\n=== bad: {name} ===")
    rc, out, err = generate(os.path.join(HERE, header))
    report("generator exits non-zero", rc != 0, f"rc={rc}")
    combined = (err + out).lower()
    report(f"error mentions {expected_keyword!r}",
           expected_keyword.lower() in combined,
           f"stderr/stdout: {err.strip() or out.strip()[:200]}")


# ----------------------------------------------------------------------------

def main():
    test_basics()
    test_nested()
    test_arrays()
    test_strings()
    test_anonymous()
    test_attributes()
    test_multitoken()
    test_endian_flag()
    test_typedef_alias()
    test_nested_array()
    test_string_literal_keyword()
    test_forward_decl()
    test_default_ctor()
    test_includes()
    test_bad("pointer",      "bad_pointer.h",      "pointer")
    test_bad("bitfield",     "bad_bitfield.h",     "bit field")
    test_bad("unknown type", "bad_unknown_type.h", "unknown type")
    test_bad("truncated",    "bad_truncated.h",    "unmatched")
    print(f"\n----- {PASS} passed, {FAIL} failed -----")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
