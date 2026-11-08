#!/usr/bin/env python3
"""Convert an SVG logo into filled outlines only (standard library only).

Usage: python3 tools/outline_svg.py in.svg out.svg [--width MM]

Every visible shape becomes area: strokes are replaced by their outline
(round caps and round joins, honouring stroke-width and group transforms),
fills are kept (nonzero rule), and everything is united into simple,
non-overlapping loops (outer boundaries and holes). The result is written
as one filled path (fill-rule evenodd) in the input's user units, with a
viewBox tight around the geometry, so "width" of the output is the width
of the logo itself. Curves are flattened to line segments (chord error
<= --tol user units, default 0.01).

Prints the bounding box and the total filled area, also in mm^2 for the
target width (--width, default 80 mm; the scale is width / bbox width).

Supported input (what the OE5XRX logo uses, plus a little more): <g>,
<path> (M L H V Q T C S A Z, absolute and relative), <circle>, <rect>,
<ellipse>, <polygon>, <polyline>, <line>; transform translate/scale/
rotate/matrix; fill, stroke, stroke-width, stroke-linecap/linejoin as
attributes or in style="". Strokes need round caps and joins and a
similarity transform; anything else raises an error instead of guessing.
"""
import argparse
import math
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "{http://www.w3.org/2000/svg}"
INHERITED = ("fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
             "fill-rule", "display", "visibility")


class OutlineError(Exception):
    pass


# ---------------------------------------------------------------- transforms
def mat_mul(a, b):
    """a * b for affine matrices (a, b, c, d, e, f) as in SVG matrix()."""
    a1, b1, c1, d1, e1, f1 = a
    a2, b2, c2, d2, e2, f2 = b
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def parse_transform(s):
    m = IDENTITY
    for name, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(x) for x in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", args)]
        if name == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif name == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif name == "rotate":
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = mat_mul(mat_mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name == "matrix":
            t = tuple(v)
        else:
            raise OutlineError(f"unsupported transform {name}()")
        m = mat_mul(m, t)
    return m


def apply(m, p):
    a, b, c, d, e, f = m
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def similarity_scale(m):
    """Uniform scale factor of m; raise if m is not a similarity transform."""
    a, b, c, d, _, _ = m
    sx, sy = math.hypot(a, b), math.hypot(c, d)
    if abs(sx - sy) > 1e-9 * max(sx, sy) or abs(a * c + b * d) > 1e-9 * sx * sy:
        raise OutlineError("strokes under a non-uniform transform are not supported")
    return sx


# ------------------------------------------------------------- path parsing
TOKEN = re.compile(r"([MmLlHhVvQqTtCcSsAaZz])|([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")


def tokenize(d):
    for cmd, num in TOKEN.findall(d):
        yield cmd if cmd else float(num)


def parse_path(d):
    """Return subpaths: list of (segments, closed). A segment is
    ('L', p0, p1) | ('Q', p0, c, p1) | ('C', p0, c1, c2, p1) |
    ('A', p0, rx, ry, phi, large, sweep, p1)."""
    toks = list(tokenize(d))
    i, cmd = 0, None
    cur = start = (0.0, 0.0)
    last_ctrl, last_cmd = None, None
    subs, segs = [], []

    def nums(n):
        nonlocal i
        if i + n > len(toks) or any(isinstance(t, str) for t in toks[i:i + n]):
            raise OutlineError(f"bad path data near token {i}")
        v = toks[i:i + n]
        i += n
        return v

    def close_sub(closed):
        nonlocal segs
        if segs:
            subs.append((segs, closed))
        segs = []

    while i < len(toks):
        if isinstance(toks[i], str):
            cmd = toks[i]
            i += 1
        elif cmd is None:
            raise OutlineError("path data must start with a command")
        rel = cmd.islower()
        C = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if C == "Z":
            if cur != start:
                segs.append(("L", cur, start))
            close_sub(True)
            cur = start
            last_cmd = "Z"
            cmd = None
            continue
        if C == "M":
            x, y = nums(2)
            close_sub(False)
            cur = start = (ox + x, oy + y)
            cmd = "l" if rel else "L"  # following pairs are lineto
            last_cmd = "M"
            continue
        if C == "L":
            x, y = nums(2)
            p = (ox + x, oy + y)
            segs.append(("L", cur, p))
        elif C == "H":
            (x,) = nums(1)
            p = (ox + x, cur[1])
            segs.append(("L", cur, p))
        elif C == "V":
            (y,) = nums(1)
            p = (cur[0], oy + y)
            segs.append(("L", cur, p))
        elif C in "QT":
            if C == "Q":
                cx, cy, x, y = nums(4)
                c = (ox + cx, oy + cy)
            else:
                x, y = nums(2)
                c = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) \
                    if last_cmd in ("Q", "T") else cur
            p = (ox + x, oy + y)
            segs.append(("Q", cur, c, p))
            last_ctrl = c
        elif C in "CS":
            if C == "C":
                x1, y1, x2, y2, x, y = nums(6)
                c1 = (ox + x1, oy + y1)
            else:
                x2, y2, x, y = nums(4)
                c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) \
                    if last_cmd in ("C", "S") else cur
            c2 = (ox + x2, oy + y2)
            p = (ox + x, oy + y)
            segs.append(("C", cur, c1, c2, p))
            last_ctrl = c2
        elif C == "A":
            rx, ry, phi, large, sweep, x, y = nums(7)
            p = (ox + x, oy + y)
            segs.append(("A", cur, abs(rx), abs(ry), phi, bool(large), bool(sweep), p))
        else:
            raise OutlineError(f"unsupported path command {cmd}")
        cur = p
        last_cmd = C
    close_sub(False)
    return subs


# ------------------------------------------------- sampling of one segment
def arc_center(p0, rx, ry, phi_deg, large, sweep, p1):
    """SVG endpoint arc -> (cx, cy, rx, ry, phi, theta1, dtheta) (SVG F.6.5)."""
    phi = math.radians(phi_deg)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1 = cp * dx + sp * dy
    y1 = -sp * dx + cp * dy
    lam = (x1 / rx) ** 2 + (y1 / ry) ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    k = math.sqrt(max(0.0, num / den)) if den else 0.0
    if large == sweep:
        k = -k
    cx1, cy1 = k * rx * y1 / ry, -k * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    return cx, cy, rx, ry, phi, t1, dt


def sample_segment(seg, tol):
    """Points and unit tangents along a segment: list of ((x, y), (tx, ty))."""
    kind = seg[0]
    if kind == "L":
        p0, p1 = seg[1], seg[2]
        L = math.dist(p0, p1)
        if L == 0:
            return [(p0, None), (p1, None)]
        t = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
        return [(p0, t), (p1, t)]
    if kind == "A":
        p0, rx, ry, phi, large, sweep, p1 = seg[1:]
        if rx == 0 or ry == 0 or p0 == p1:
            return sample_segment(("L", p0, p1), tol)
        cx, cy, rx, ry, ph, t1, dt = arc_center(p0, rx, ry, phi, large, sweep, p1)
        r = max(rx, ry)
        step = 2 * math.acos(max(-1.0, 1 - tol / r)) if tol < r else math.pi / 2
        n = max(2, math.ceil(abs(dt) / step))
        cp, sp = math.cos(ph), math.sin(ph)
        out = []
        for k in range(n + 1):
            t = t1 + dt * k / n
            ex, ey = rx * math.cos(t), ry * math.sin(t)
            p = (cx + cp * ex - sp * ey, cy + sp * ex + cp * ey)
            dx, dy = -rx * math.sin(t), ry * math.cos(t)
            tx, ty = cp * dx - sp * dy, sp * dx + cp * dy
            if dt < 0:
                tx, ty = -tx, -ty
            ln = math.hypot(tx, ty)
            out.append((p, (tx / ln, ty / ln)))
        out[0] = (p0, out[0][1])
        out[-1] = (p1, out[-1][1])
        return out
    if kind in ("Q", "C"):
        pts = seg[1:]
        deg = len(pts) - 1

        def at(t):
            q = list(pts)
            while len(q) > 1:
                q = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1])
                     for a, b in zip(q, q[1:])]
            return q[0]

        def tangent(t):
            d = [((b[0] - a[0]) * deg, (b[1] - a[1]) * deg) for a, b in zip(pts, pts[1:])]
            q = d
            while len(q) > 1:
                q = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1])
                     for a, b in zip(q, q[1:])]
            ln = math.hypot(*q[0])
            return (q[0][0] / ln, q[0][1] / ln) if ln else None

        # second-derivative bound for the chord error: n >= sqrt(|P''| / (8 tol))
        if deg == 2:
            dd = math.hypot(2 * (pts[0][0] - 2 * pts[1][0] + pts[2][0]),
                            2 * (pts[0][1] - 2 * pts[1][1] + pts[2][1]))
        else:
            dd = 6 * max(math.hypot(pts[i][0] - 2 * pts[i + 1][0] + pts[i + 2][0],
                                    pts[i][1] - 2 * pts[i + 1][1] + pts[i + 2][1])
                         for i in range(2))
        n = max(1, math.ceil(math.sqrt(dd / (8 * tol))))
        out = [(at(k / n), tangent(k / n)) for k in range(n + 1)]
        out[0] = (pts[0], out[0][1])
        out[-1] = (pts[-1], out[-1][1])
        return out
    raise OutlineError(f"unknown segment {kind}")


def flatten_subpath(segs, tol):
    pts = []
    for seg in segs:
        s = [p for p, _ in sample_segment(seg, tol)]
        pts.extend(s if not pts else s[1:])
    return pts


def round_cap(center, frm, to, h, tol):
    """Points on the half circle of radius h from angle frm to angle to (ccw if to>frm)."""
    step = 2 * math.acos(max(-1.0, 1 - tol / h)) if tol < h else math.pi / 2
    n = max(2, math.ceil(abs(to - frm) / step))
    return [(center[0] + h * math.cos(frm + (to - frm) * k / n),
             center[1] + h * math.sin(frm + (to - frm) * k / n)) for k in range(1, n)]


def stroke_segment(seg, h, tol):
    """Outline of one segment stroked with half-width h and round caps: a ring."""
    s = sample_segment(seg, tol)
    if all(t is None for _, t in s):  # zero-length segment: a round dot
        c = s[0][0]
        return [(c[0] + h, c[1])] + round_cap(c, 0, 2 * math.pi, h, tol)
    left, right = [], []
    for p, t in s:
        nx, ny = -t[1], t[0]
        left.append((p[0] + nx * h, p[1] + ny * h))
        right.append((p[0] - nx * h, p[1] - ny * h))
    if seg[0] in ("Q", "C", "A"):
        # inner offset is only valid while curvature radius > h (checked for arcs)
        if seg[0] == "A":
            *_, rx, ry, _, _, _ = arc_center(*seg[1:])
            if min(rx, ry) <= h:
                raise OutlineError("arc radius not larger than half the stroke width")
    a_end = math.atan2(s[-1][1][1], s[-1][1][0])
    a_start = math.atan2(s[0][1][1], s[0][1][0])
    ring = list(left)
    # end cap: from the left side round the front to the right side
    ring += round_cap(s[-1][0], a_end + math.pi / 2, a_end - math.pi / 2, h, tol)
    ring += right[::-1]
    # start cap: from the right side round the back to the left side
    ring += round_cap(s[0][0], a_start - math.pi / 2, a_start - 3 * math.pi / 2, h, tol)
    return ring


# --------------------------------------------------------- element walking
def style_of(el, parent):
    st = dict(parent)
    for k in INHERITED:
        if k in el.attrib:
            st[k] = el.attrib[k].strip()
    for decl in el.attrib.get("style", "").split(";"):
        if ":" in decl:
            k, v = (x.strip() for x in decl.split(":", 1))
            if k in INHERITED:
                st[k] = v
    return st


def element_subpaths(el, tag):
    a = el.attrib
    f = lambda k, d=0.0: float(a.get(k, d))
    if tag == "path":
        return parse_path(a.get("d", ""))
    if tag in ("circle", "ellipse"):
        cx, cy = f("cx"), f("cy")
        rx = f("r") if tag == "circle" else f("rx")
        ry = f("r") if tag == "circle" else f("ry")
        p0, p1 = (cx + rx, cy), (cx - rx, cy)
        return [([("A", p0, rx, ry, 0, False, True, p1),
                  ("A", p1, rx, ry, 0, False, True, p0)], True)]
    if tag == "rect":
        x, y, w, h = f("x"), f("y"), f("width"), f("height")
        if f("rx") or f("ry"):
            raise OutlineError("rounded <rect> is not supported")
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        return [([("L", pts[i], pts[(i + 1) % 4]) for i in range(4)], True)]
    if tag == "line":
        return [([("L", (f("x1"), f("y1")), (f("x2"), f("y2")))], False)]
    if tag in ("polygon", "polyline"):
        v = [float(x) for x in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?",
                                          a.get("points", ""))]
        pts = list(zip(v[0::2], v[1::2]))
        segs = [("L", p, q) for p, q in zip(pts, pts[1:])]
        if tag == "polygon" and pts:
            segs.append(("L", pts[-1], pts[0]))
        return [(segs, tag == "polygon")]
    return []


def collect(root, tol):
    """Return a list of shapes; each shape is a list of rings (nonzero rule),
    in root user units."""
    shapes = []

    def walk(el, m, st):
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("defs", "title", "desc", "metadata", "style", "clipPath", "mask"):
            return
        if tag == "use":
            raise OutlineError("<use> is not supported")
        st = style_of(el, st)
        if st.get("display") == "none" or st.get("visibility") == "hidden":
            return
        m = mat_mul(m, parse_transform(el.attrib.get("transform")))
        subs = element_subpaths(el, tag)
        if subs:
            if st.get("fill", "black") != "none":
                if st.get("fill-rule", "nonzero") != "nonzero":
                    raise OutlineError("only fill-rule nonzero is supported")
                rings = [[apply(m, p) for p in flatten_subpath(segs, tol / similarity_scale(m)
                          if _is_sim(m) else tol)] for segs, _ in subs]
                shapes.append([r for r in rings if len(r) >= 3])
            if st.get("stroke", "none") != "none":
                w = float(st.get("stroke-width", "1"))
                if w > 0:
                    if st.get("stroke-linecap", "butt") != "round" or \
                            st.get("stroke-linejoin", "miter") != "round":
                        raise OutlineError("only round stroke caps and joins are supported")
                    k = similarity_scale(m)
                    for segs, _ in subs:
                        for seg in segs:
                            ring = stroke_segment(seg, w / 2, tol / k)
                            shapes.append([[apply(m, p) for p in ring]])
        for ch in el:
            walk(ch, m, st)

    walk(root, IDENTITY, {})
    return [s for s in shapes if s]


def _is_sim(m):
    try:
        similarity_scale(m)
        return True
    except OutlineError:
        return False


# ------------------------------------------------------------------ union
def ring_edges(ring):
    return [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))
            if ring[i] != ring[(i + 1) % len(ring)]]


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def winding(rings, p):
    x, y = p
    w = 0
    for r in rings:
        n = len(r)
        for i in range(n):
            (x0, y0), (x1, y1) = r[i], r[(i + 1) % n]
            if y0 <= y < y1 or y1 <= y < y0:
                xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                if xi > x:
                    w += 1 if y1 > y0 else -1
    return w


def union(shapes):
    """United boundary of all shapes as loops, each with the area on its left
    in a y-down frame... returned as plain lists; orientation fixed later."""
    eps = 1e-9
    edges = []  # (p, q, shape index)
    for si, sh in enumerate(shapes):
        for r in sh:
            for p, q in ring_edges(r):
                edges.append([p, q, si])
    boxes = [(min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
             for p, q, _ in edges]
    splits = [[] for _ in edges]
    order = sorted(range(len(edges)), key=lambda i: boxes[i][0])
    for oi, i in enumerate(order):
        bi = boxes[i]
        p, q, _ = edges[i]
        for j in order[oi + 1:]:
            bj = boxes[j]
            if bj[0] > bi[2] + eps:
                break
            if bj[1] > bi[3] + eps or bj[3] < bi[1] - eps:
                continue
            r, s, _ = edges[j]
            _intersect(p, q, r, s, i, j, splits, eps)
    pieces = []
    for (p, q, si), sp in zip(edges, splits):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        pts = sorted(set(sp), key=lambda t: ((t[0] - p[0]) * dx + (t[1] - p[1]) * dy) / L2)
        chain = [p] + [t for t in pts if t != p and t != q] + [q]
        for a, b in zip(chain, chain[1:]):
            if a != b:
                pieces.append((a, b))
    sboxes = [bbox([pt for r in sh for pt in r]) for sh in shapes]

    def inside(pt):
        for sb, sh in zip(sboxes, shapes):
            if sb[0] <= pt[0] <= sb[2] and sb[1] <= pt[1] <= sb[3] and winding(sh, pt) != 0:
                return True
        return False

    kept = {}
    for a, b in pieces:
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = math.dist(a, b)
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        d = min(1e-6, L / 4)
        il = inside((mx + nx * d, my + ny * d))
        ir = inside((mx - nx * d, my - ny * d))
        if il and not ir:
            kept[(a, b)] = True
        elif ir and not il:
            kept[(b, a)] = True
    return chain_loops(list(kept))


def _intersect(p, q, r, s, i, j, splits, eps):
    d1 = (q[0] - p[0], q[1] - p[1])
    d2 = (s[0] - r[0], s[1] - r[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    l1, l2 = math.hypot(*d1), math.hypot(*d2)
    # endpoints lying on the other segment (T-junctions, collinear overlaps)
    for pt, (a, b, la, k) in ((r, (p, q, l1, i)), (s, (p, q, l1, i)),
                              (p, (r, s, l2, j)), (q, (r, s, l2, j))):
        ex, ey = b[0] - a[0], b[1] - a[1]
        t = ((pt[0] - a[0]) * ex + (pt[1] - a[1]) * ey) / (la * la)
        if 0 < t < 1 and abs((pt[0] - a[0]) * ey - (pt[1] - a[1]) * ex) / la < eps:
            splits[k].append(pt)
    if abs(den) < 1e-15 * l1 * l2:
        return
    t = ((r[0] - p[0]) * d2[1] - (r[1] - p[1]) * d2[0]) / den
    u = ((r[0] - p[0]) * d1[1] - (r[1] - p[1]) * d1[0]) / den
    if eps / l1 < t < 1 - eps / l1 and eps / l2 < u < 1 - eps / l2:
        x = (p[0] + t * d1[0], p[1] + t * d1[1])
        splits[i].append(x)
        splits[j].append(x)


def chain_loops(edges):
    out = {}
    for a, b in edges:
        out.setdefault(a, []).append(b)
    loops = []
    while out:
        start = next(iter(out))
        loop = [start]
        prev, cur = None, start
        while True:
            nxt = out[cur]
            if len(nxt) == 1:
                b = nxt.pop()
            else:  # touching loops: take the sharpest turn to keep loops simple
                ax, ay = (cur[0] - prev[0], cur[1] - prev[1]) if prev else (1, 0)
                b = max(nxt, key=lambda c: _turn(ax, ay, c[0] - cur[0], c[1] - cur[1]))
                nxt.remove(b)
            if not out[cur]:
                del out[cur]
            if b == start:
                break
            loop.append(b)
            prev, cur = cur, b
            if cur not in out:
                raise OutlineError("open boundary chain (numerical problem)")
        loops.append(loop)
    return loops


def _turn(ax, ay, bx, by):
    # area-on-left convention: prefer the leftmost (ccw in y-up math sense) turn
    return math.atan2(ax * by - ay * bx, ax * bx + ay * by)


def simplify(loop, eps=1e-9):
    """Drop vertices that are exactly collinear with their neighbours."""
    out = []
    n = len(loop)
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
        if abs(cross) > eps * math.dist(a, b) * math.dist(b, c) or dot < 0:
            out.append(b)
    return out


def signed_area(loop):
    return sum(loop[i - 1][0] * loop[i][1] - loop[i][0] * loop[i - 1][1]
               for i in range(len(loop))) / 2


# -------------------------------------------------------------------- main
def outline(svg_text, tol=0.01):
    root = ET.fromstring(svg_text)
    shapes = collect(root, tol)
    loops = [simplify(l) for l in union(shapes)]
    loops = [l for l in loops if len(l) >= 3]
    return loops


def to_svg(loops, digits=5):
    allpts = [p for l in loops for p in l]
    x0, y0, x1, y1 = bbox(allpts)
    fmt = lambda v: f"{v:.{digits}f}".rstrip("0").rstrip(".")
    d = " ".join("M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in l) + " Z" for l in loops)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{fmt(x0)} {fmt(y0)} '
            f'{fmt(x1 - x0)} {fmt(y1 - y0)}" width="{fmt(x1 - x0)}" height="{fmt(y1 - y0)}">\n'
            f'  <path fill="#000" fill-rule="evenodd" d="{d}"/>\n</svg>\n')


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--width", type=float, default=80.0, help="target width in mm")
    ap.add_argument("--tol", type=float, default=0.01, help="chord error in user units")
    a = ap.parse_args(argv)
    with open(a.inp, encoding="utf-8") as f:
        loops = outline(f.read(), a.tol)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(to_svg(loops))
    x0, y0, x1, y1 = bbox([p for l in loops for p in l])
    area = abs(sum(signed_area(l) for l in loops))
    k = a.width / (x1 - x0)
    print(f"loops: {len(loops)}  vertices: {sum(map(len, loops))}")
    print(f"bbox (user units): {x0:.4f} {y0:.4f} .. {x1:.4f} {y1:.4f}  "
          f"size {x1 - x0:.4f} x {y1 - y0:.4f}")
    print(f"area (user units^2): {area:.4f}")
    print(f"at width {a.width:g} mm: scale {k:.6f} mm/unit, size {a.width:g} x "
          f"{(y1 - y0) * k:.4f} mm, area {area * k * k:.4f} mm^2")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except OutlineError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
