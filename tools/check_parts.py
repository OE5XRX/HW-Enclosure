#!/usr/bin/env python3
"""Open each part / assembly in SolidCraft and verify features and measurements.

Usage: python3 tools/check_parts.py [name ...]   (default: all parts and assemblies)
Exit 0 only if every named part opens, has no feature error, no rolled_back
feature, and matches its expected volume / bounding box / centre of mass.
Exit 1 on a failed check, exit 2 if SolidCraft is not reachable (start it with
`solidcraft --control 7878`) or solidcraft-cli is missing.
An assembly passes when it opens without feature errors or rolled_back features,
has exactly the expected top-level occurrences (count and names), every
occurrence's bounding-box centre is within tolerance of the centre implied by
reference/assembly.md, and every linked component's file is found.
"""
import math
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
    tol_vol: float = 0.5  # mm^3, absolute
    tol_len: float = 0.05  # mm, bbox
    tol_com: float = 0.05  # mm


EXPECTED = {
    "desktop/parts/leiste.sc": Expect(3419.76, (-68, -4.25, 0), (68, 4.25, 3)),
    # plate 38513.53 + branding logo outline 855.83 mm^2 (80 mm wide) x logo_h 0.6
    "desktop/parts/deckplatte.sc": Expect(38513.53 + 855.83 * 0.6, (-58.5, -55, 0), (58.5, 55, 3.6)),
    "desktop/parts/grundgestell-gespiegelt.sc":
        Expect(97892.06, (-68, -60, 0), (68, 60, 20), com_x=1.957),
    "desktop/parts/grundgestell.sc":
        Expect(97892.06, (-68, -60, 0), (68, 60, 20), com_x=-1.957),
}



# ---------------------------------------------------------------- assemblies

@dataclass
class Occ:
    """One top-level occurrence: local bbox of its source, then the placement
    from reference/assembly.md: rotations (axis, deg) applied in order about the
    fixed assembly axes (extrinsic), then translation."""
    name: str
    local_min: tuple
    local_max: tuple
    rot: tuple
    t: tuple


def _rot(axis, deg):
    c, s = round(math.cos(math.radians(deg)), 12), round(math.sin(math.radians(deg)), 12)
    return {"x": [[1, 0, 0], [0, c, -s], [0, s, c]],
            "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
            "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[axis]


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def placement(rot):
    """Rotation matrix for extrinsic rotations in listed order: R = Rn ... R1."""
    r = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    for axis, deg in rot:
        assert deg % 90 == 0, "bbox centre mapping needs quarter turns"
        r = _mul(_rot(axis, deg), r)
    return r


def matrix(occ):
    """Row-major 3x4 [R | t] (as occurrence.move / file.insert_step take it)."""
    r = placement(occ.rot)
    return [r[i] + [occ.t[i]] for i in range(3)]


def expected_centre(occ):
    """Quarter-turn rotations map an axis-aligned bbox onto one, so the
    centre maps to the centre: c' = R c + t."""
    c = [(a + b) / 2 for a, b in zip(occ.local_min, occ.local_max)]
    r = placement(occ.rot)
    return [sum(r[i][k] * c[k] for k in range(3)) + occ.t[i] for i in range(3)]


@dataclass
class AssemblyExpect:
    occurrences: list
    tol_centre: float = 0.1  # mm


def _part_bbox(rel):
    e = EXPECTED[rel]
    return e.bbox_min, e.bbox_max


# Local bboxes of the PCB STEPs (whole occurrence incl. components, STEP
# origin = KiCad page origin, y = -KiCad y), measured after file.insert_step
# at identity; the board outlines match reference/assembly.md E8 exactly.
STEP_BBOX = {
    "BusBoard": ((65.284, -125.396, -1.5988), (182.65, -25.396, 13.2012)),
    "PowerBoard": ((99.568, -140.64, -1.0988), (205.994, -40.64, 10.0012)),
    "CM4Carrier": ((93.222, -145.794, -1.4488), (199.648, -45.794, 15.1012)),
    "FMTransceiver": ((85.217, -136.271, -1.9788), (204.343, -36.271, 9.9012)),
}

_GESTELL = _part_bbox("desktop/parts/grundgestell.sc")
_GESP = _part_bbox("desktop/parts/grundgestell-gespiegelt.sc")
_PLATTE = _part_bbox("desktop/parts/deckplatte.sc")
_LEISTE = _part_bbox("desktop/parts/leiste.sc")
_MOD = (("x", -90), ("z", -90))

# Placements copied from the occurrence table in reference/assembly.md.
STATION = [
    Occ("Gestell", *_GESTELL, (), (0, 0, 0)),
    Occ("Gestell-gespiegelt", *_GESP, (("y", 180),), (0, 0, 110)),
    Occ("Deckplatte-links", *_PLATTE, (("x", 90), ("z", -90)), (-68, 4.5, 55)),
    Occ("Deckplatte-rechts", *_PLATTE, (("x", -90), ("z", -90)), (68, 4.5, 55)),
    Occ("Leiste-1", *_LEISTE, (("x", -90),), (0, 60, 4.25)),
    Occ("Leiste-2", *_LEISTE, (("x", -90), ("y", 180)), (0, 60, 105.75)),
    Occ("Leiste-3", *_LEISTE, (("x", -90), ("z", 180)), (0, -55.6012, 9.75)),
    Occ("Leiste-4", *_LEISTE, (("x", 90),), (0, -55.6012, 100.25)),
    Occ("BusBoard", *STEP_BBOX["BusBoard"], (("x", -90),), (-125.284, -55.6012, -20.396)),
    Occ("Slot1-PowerBoard", *STEP_BBOX["PowerBoard"], _MOD, (-57.1212, 157.194, -35.64)),
    Occ("Slot2-CM4Carrier", *STEP_BBOX["CM4Carrier"], _MOD, (-37.1212, 150.848, -40.794)),
    Occ("Slot3-FMTransceiver", *STEP_BBOX["FMTransceiver"], _MOD, (-17.1212, 155.543, -31.271)),
    Occ("Slot4-FMTransceiver", *STEP_BBOX["FMTransceiver"], _MOD, (2.8788, 155.543, -31.271)),
    Occ("Slot5-FMTransceiver", *STEP_BBOX["FMTransceiver"], _MOD, (22.8788, 155.543, -31.271)),
    Occ("Slot6-FMTransceiver", *STEP_BBOX["FMTransceiver"], _MOD, (42.8788, 155.543, -31.271)),
]

ASSEMBLIES = {
    "desktop/station.sc": AssemblyExpect(STATION),
}


def compare_assembly(exp, timeline, found, links):
    """found: {occurrence base name: (bbox_min, bbox_max)} of the top-level
    occurrences; links: component.links entries. Returns problem strings."""
    problems = []
    for f in timeline:
        if f.get("error"):
            problems.append(f"error: {f.get('name')}: {f['error']}")
        if f.get("rolled_back"):
            problems.append(f"rolled_back: {f.get('name')}")
    want = {o.name for o in exp.occurrences}
    if len(found) != len(exp.occurrences):
        problems.append(f"occurrence count {len(found)} != {len(exp.occurrences)}")
    for n in sorted(set(found) - want):
        problems.append(f"unexpected occurrence: {n}")
    for o in exp.occurrences:
        if o.name not in found:
            problems.append(f"missing occurrence: {o.name}")
            continue
        lo, hi = found[o.name]
        got = [(a + b) / 2 for a, b in zip(lo, hi)]
        ec = expected_centre(o)
        if any(abs(g - e) > exp.tol_centre for g, e in zip(got, ec)):
            problems.append(f"{o.name}: bbox centre {[round(g, 3) for g in got]}"
                            f" != {[round(e, 3) for e in ec]} (+-{exp.tol_centre})")
    for ln in links:
        if ln.get("found") is not True:
            problems.append(f"link not found: {ln.get('name')} -> {ln.get('path')}")
    return problems


def check_assembly(sc, rel, exp):
    path = os.path.join(ROOT, rel)
    try:
        sc.open(path)
        timeline = sc.timeline()
        comps = sc.execute("component.list", {"compact": True})["components"]
        found = {}
        for c in comps:
            for o in c.get("occurrences", []):
                if o.get("parent") != 0:
                    continue
                base = o["name"].rsplit(":", 1)[0]
                if base in found:
                    base = o["name"]  # second placement of one component
                bb = sc.execute("occurrence.properties",
                                {"occurrence": o["id"]})["total"]["bbox"]
                found[base] = (bb["min"], bb["max"])
        links = sc.execute("component.links", {}).get("links", [])
    except Exception as e:  # SolidCraftError etc.
        return [f"open/inspect failed: {e}"]
    return compare_assembly(exp, timeline, found, links)

def compare(exp, body, timeline):
    """Return a list of problem strings (empty means PASS)."""
    problems = []
    for f in timeline:
        if f.get("error"):
            problems.append(f"error: {f.get('name')}: {f['error']}")
        if f.get("rolled_back"):
            problems.append(f"rolled_back: {f.get('name')}")
    vol = body["volume_mm3"]
    if abs(vol - exp.volume) > exp.tol_vol:
        problems.append(f"volume {vol:.2f} != {exp.volume:.2f} (+-{exp.tol_vol} mm^3)")
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
    table = {**EXPECTED, **ASSEMBLIES}
    names = argv or list(table)
    selected = {}
    for n in names:
        hits = [k for k in table if k == n or os.path.basename(k) in (n, n + ".sc")]
        if not hits:
            print(f"unknown part: {n}")
            return 2
        for k in hits:
            selected[k] = table[k]
    # Files first: do not need the app to report missing parts.
    missing = [k for k in selected if not os.path.exists(os.path.join(ROOT, k))]
    if missing:
        for k in missing:
            print(f"FAIL {k}: file not found")
        return 1
    from sc_mcp import SolidCraft, SolidCraftError
    try:
        sc = SolidCraft(allow_paths=[ROOT])
        sc.inspect()  # the constructor is lazy: probe that the app is reachable
    except (SolidCraftError, OSError) as e:
        print(f"SolidCraft läuft nicht — starte `solidcraft --control 7878` ({e})")
        return 2
    ok = True
    try:
        for rel, exp in selected.items():
            if isinstance(exp, AssemblyExpect):
                problems = check_assembly(sc, rel, exp)
            else:
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
