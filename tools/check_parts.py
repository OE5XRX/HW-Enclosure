#!/usr/bin/env python3
"""Open each part in SolidCraft and verify features and measurements.

Usage: python3 tools/check_parts.py [name ...]   (default: all parts)
Exit 0 only if every named part opens, has no feature error, no rolled_back
feature, and matches its expected volume / bounding box / centre of mass.
"""
import os
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class Expect:
    volume: float
    bbox_min: tuple
    bbox_max: tuple
    com_x: float | None = None
    tol_vol: float = 0.5  # percent of volume
    tol_len: float = 0.05  # mm, bbox
    tol_com: float = 0.05  # mm


EXPECTED = {
    "desktop/parts/leiste.sc": Expect(3419.76, (-68, -4.25, 0), (68, 4.25, 3)),
    "desktop/parts/deckplatte.sc": Expect(39783.31, (-58.5, -55, 0), (58.5, 55, 3.6)),
    "desktop/parts/grundgestell-gespiegelt.sc":
        Expect(97892.06, (-68, -60, 0), (68, 60, 20), com_x=1.957),
}


def compare(exp, body, timeline):
    """Return a list of problem strings (empty means PASS)."""
    problems = []
    for f in timeline:
        if f.get("error"):
            problems.append(f"error: {f.get('name')}: {f['error']}")
        if f.get("rolled_back"):
            problems.append(f"rolled_back: {f.get('name')}")
    vol = body["volume_mm3"]
    if abs(vol - exp.volume) > exp.volume * exp.tol_vol / 100:
        problems.append(f"volume {vol:.2f} != {exp.volume} (+-{exp.tol_vol}%)")
    for label, got, want in (("bbox_min", body["bbox"]["min"], exp.bbox_min),
                             ("bbox_max", body["bbox"]["max"], exp.bbox_max)):
        if any(abs(g - w) > exp.tol_len for g, w in zip(got, want)):
            problems.append(f"{label} {[round(g, 3) for g in got]} != {list(want)}")
    if exp.com_x is not None:
        cx = body["center_of_mass"][0]
        if abs(cx - exp.com_x) > exp.tol_com:
            problems.append(f"com_x {cx:.3f} != {exp.com_x}")
    return problems


def check(sc, rel, exp):
    path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return [f"file not found: {rel}"]
    try:
        sc.open(path)
        timeline = sc.timeline()
        m = sc.measure()
    except Exception as e:  # SolidCraftError etc.
        return [f"open/measure failed: {e}"]
    bodies = m.get("bodies", [])
    if len(bodies) != 1:
        return [f"expected 1 body, found {len(bodies)}"]
    return compare(exp, bodies[0], timeline)


def main(argv):
    names = argv or list(EXPECTED)
    selected = {}
    for n in names:
        hits = [k for k in EXPECTED if k == n or os.path.basename(k) in (n, n + ".sc")]
        if not hits:
            print(f"unknown part: {n}")
            return 2
        for k in hits:
            selected[k] = EXPECTED[k]
    # Files first: do not need the app to report missing parts.
    missing = [k for k in selected if not os.path.exists(os.path.join(ROOT, k))]
    if missing:
        for k in missing:
            print(f"FAIL {k}: file not found")
        return 1
    from sc_mcp import SolidCraft
    sc = SolidCraft(allow_paths=[ROOT])
    ok = True
    try:
        for rel, exp in selected.items():
            problems = check(sc, rel, exp)
            print(f"{'PASS' if not problems else 'FAIL'} {rel}")
            for p in problems:
                print(f"     {p}")
            ok = ok and not problems
    finally:
        sc.close()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
