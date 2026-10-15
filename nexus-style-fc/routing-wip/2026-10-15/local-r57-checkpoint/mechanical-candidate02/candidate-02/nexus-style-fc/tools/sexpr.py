"""Minimal S-expression reader/writer for KiCad files (strings, atoms, nested lists)."""


def parse(text):
    """Parse a KiCad S-expression into nested lists; strings become ('s', value) tuples."""
    pos, n = 0, len(text)
    stack, cur = [], []
    while pos < n:
        c = text[pos]
        if c == "(":
            stack.append(cur)
            cur = []
            pos += 1
        elif c == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while text[pos] != '"':
                if text[pos] == "\\":
                    pos += 1
                buf.append(text[pos])
                pos += 1
            cur.append(("s", "".join(buf)))
            pos += 1
        elif c.isspace():
            pos += 1
        else:
            start = pos
            while pos < n and not text[pos].isspace() and text[pos] not in '()"':
                pos += 1
            cur.append(text[start:pos])
    return cur[0] if len(cur) == 1 else cur


def dump(node, indent=0):
    """Serialise nested lists back to KiCad-style text."""
    if isinstance(node, tuple):
        return '"' + node[1].replace("\\", "\\\\").replace('"', '\\"') + '"'
    if not isinstance(node, list):
        return str(node)
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return "(" + " ".join(dump(x) for x in node) + ")"
    pad = "\t" * (indent + 1)
    parts = ["(" + " ".join(dump(x) for x in node if not isinstance(x, list))]
    for x in node:
        if isinstance(x, list):
            parts.append("\n" + pad + dump(x, indent + 1))
    return "".join(parts) + "\n" + "\t" * indent + ")"


def text(node):
    return node[1] if isinstance(node, tuple) else node


def find(node, key):
    """Direct children lists whose head is `key`."""
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def walk(node, key):
    """All descendant lists whose head is `key`."""
    out = []
    for x in node:
        if isinstance(x, list):
            if x and x[0] == key:
                out.append(x)
            out.extend(walk(x, key))
    return out


def symbol_from_lib(lib_path, name):
    """Return the top-level (symbol "name" ...) list from a .kicad_sym library."""
    lib = parse(open(lib_path, encoding="utf-8").read())
    for s in find(lib, "symbol"):
        if text(s[1]) == name:
            return s
    raise KeyError(f"{name} not in {lib_path}")


def symbol_pins(sym):
    """{pin number: (x, y, angle, length, name)} in symbol coordinates (y up)."""
    pins = {}
    for p in walk(sym, "pin"):
        at = find(p, "at")[0]
        length = float(find(p, "length")[0][1]) if find(p, "length") else 2.54
        num = text(find(p, "number")[0][1])
        name = text(find(p, "name")[0][1]) if find(p, "name") else ""
        pins.setdefault(num, (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, length, name))
    return pins


def symbol_bbox(sym):
    """Rough bounding box (xmin, ymin, xmax, ymax) of a symbol in symbol coordinates."""
    xs, ys = [], []
    for p in symbol_pins(sym).values():
        xs.append(p[0])
        ys.append(p[1])
    for key in ("start", "end", "xy", "center"):
        for item in walk(sym, key):
            try:
                xs.append(float(item[1]))
                ys.append(float(item[2]))
            except (ValueError, IndexError):
                pass
    return min(xs), min(ys), max(xs), max(ys)
