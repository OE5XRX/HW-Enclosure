#!/usr/bin/env python3
"""Fit check of desktop/station.sc in the running SolidCraft app (read-only).

Usage: python3 tools/fit_check.py [--no-images] [--json PATH]

Answers the three questions of the HW-Enclosure spec with numbers taken from
the placed geometry (world coordinates, as SolidCraft reports them):

  A  groove:    every module board edge sits in the grooves of both frames
                (side clearance to each groove wall, floor gap, engagement);
  B  connector: every module socket (PCN10C-20S) mates its BusBoard header
                (PCN10-20P): pin-in-cavity offsets and side gaps for all 20
                pins, mating-face gap, axial interference of the models;
  C  holes:     the 12 BusBoard holes against the 12 back pockets.

Also: hole patterns of the cover plates and strips against their bores, and an
interference / clearance run over all placed bodies (inspect.clearance; pairs
inside one placed component are skipped). A collision is an overlap volume
> 0.01 mm^3; contact (distance 0 or overlap <= 0.01) is listed separately.

Nothing in the design is changed: only occurrence.properties, body_topology,
inspect.clearance, inspect.section (view state) and screenshots are used. If a
different design is open it must be clean; station.sc is then opened.

Writes reference/fit-check.json (default) and, unless --no-images, the
screenshots under reference/img/. Exit 0 if checks A, B and C do not fail
(a check may pass with a warning), 1 if any fails, 2 if the app is unusable.
"""
import json
import math
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_mcp import SolidCraft, SolidCraftError  # noqa: E402

STATION = os.path.join(ROOT, "desktop", "station.sc")
IMG = os.path.join(ROOT, "reference", "img")

OCCS = ["Gestell", "Gestell-gespiegelt", "Deckplatte-links", "Deckplatte-rechts",
        "Leiste-1", "Leiste-2", "Leiste-3", "Leiste-4", "BusBoard",
        "Slot1-PowerBoard", "Slot2-CM4Carrier", "Slot3-FMTransceiver",
        "Slot4-FMTransceiver", "Slot5-FMTransceiver", "Slot6-FMTransceiver"]
MODULES = [o for o in OCCS if o.startswith("Slot")]
# Slot k mates header Jx01 whose b row sits at x = -50 + 20 (k-1) (assembly.md E3).
HEADER_B_X = {m: -50.0 + 20.0 * i for i, m in enumerate(MODULES)}
FRAMES = {"bottom": "Grundgestell", "top": "Grundgestell-gespiegelt"}

COLLISION_MM3 = 0.01   # overlap above this is a collision
HOLE_TOL = 0.1         # mm, hole axis offset that still passes
PIN_TOL = 0.15         # mm, pin-to-cavity centre offset that still passes
MATE_TOL = 0.2         # mm, axial interference / mating gap that still passes


# ---------------------------------------------------------------- app access

def execute(sc, command, params, log=None):
    """execute, waiting for long requests via the `pending` tool."""
    try:
        return sc.execute(command, params)
    except SolidCraftError as e:
        if not str(e).startswith("still running"):
            raise
    while True:
        r = sc.call("pending")
        if r.get("done") is False:
            if log:
                log(f"  ... {command} still running ({r.get('running_s')} s)")
            continue
        if r.get("error"):
            raise SolidCraftError(r["error"])
        return r.get("result", r)


def ensure_station(sc):
    d = sc.inspect()
    if d.get("name") == "station" and not d.get("dirty"):
        return
    if d.get("dirty"):
        raise SolidCraftError(f"open design '{d.get('name')}' has unsaved changes")
    sc.call("open", {"path": STATION})
    if sc.inspect().get("name") != "station":
        raise SolidCraftError("could not open desktop/station.sc")


def screenshot(sc, name, **kw):
    args = {"source": "model", "grid": False, "axes": False,
            "path": os.path.join(IMG, name), **kw}
    sc.call("screenshot", args)
    return f"reference/img/{name}"


# ---------------------------------------------------------------- helpers

def r3(v):
    return round(v, 3) + 0.0  # no -0.0


def bbox(b):
    return b["bbox"]["min"], b["bbox"]["max"]


def planes(topo, axis, sign=None, ylim=None, area=None, zlim=None):
    """Planar faces whose normal is +-axis: [(coord, sign, centroid, area)]."""
    out = []
    for f in topo["faces"]:
        n = f.get("plane_normal")
        if not n or abs(abs(n[axis]) - 1) > 1e-6:
            continue
        s = 1 if n[axis] > 0 else -1
        c = f["centroid"]
        if sign is not None and s != sign:
            continue
        if ylim and not ylim[0] < c[1] < ylim[1]:
            continue
        if zlim and not zlim[0] < c[2] < zlim[1]:
            continue
        if area and not area[0] < f["area"] < area[1]:
            continue
        out.append((c[axis], s, c, f["area"]))
    return out


def cylinders(topo, radius):
    return [f["cylinder"] for f in topo["faces"]
            if f.get("cylinder") and abs(f["cylinder"]["radius"] - radius) < 1e-3]


def uniq(points, tol=1e-3):
    out = []
    for p in points:
        if all(max(abs(a - b) for a, b in zip(p, q)) > tol for q in out):
            out.append(p)
    return out


def axis_points(cyls, axis):
    """Axis positions of cylinders along `axis`, as the two other coordinates."""
    other = [i for i in range(3) if i != axis]
    return uniq([tuple(c["origin"][i] for i in other) for c in cyls
                 if abs(abs(c["axis"][axis]) - 1) < 1e-6])


def match(holes, targets):
    """Each hole to its nearest target: [(hole, target, offset)]."""
    out = []
    for h in holes:
        t = min(targets, key=lambda q: math.dist(h, q))
        out.append((h, t, math.dist(h, t)))
    return out


def intervals(faces, lo_sign):
    """Pair walls into intervals: a face of sign lo_sign at the low end,
    the next face of the other sign above it (within 2 mm)."""
    lows = sorted(f[0] for f in faces if f[1] == lo_sign)
    highs = sorted(f[0] for f in faces if f[1] == -lo_sign)
    out = []
    for lo in uniq([(v,) for v in lows]):
        hi = [h for h in highs if lo[0] < h < lo[0] + 2.0]
        if hi:
            out.append((lo[0], hi[0]))
    return out


# ---------------------------------------------------------------- checks

def check_grooves(props, topo):
    """A: board edge in the grooves of both frames."""
    walls, floors = {}, {}
    for key, frame in FRAMES.items():
        zl = (4.5, 8.5) if key == "bottom" else (101.5, 105.5)
        walls[key] = planes(topo[frame], 0, zlim=zl, area=(300, 500))
        fz = planes(topo[frame], 2, area=(250, 350), zlim=(zl[0] - 0.01, zl[1] + 0.01))
        floors[key] = fz
    rows, ok = [], True
    for m in MODULES:
        pcb = next(b for b in props[m]["bodies"] if b["name"].split(" (")[0].endswith("_PCB"))
        lo, hi = bbox(pcb)
        row = {"module": m, "board_x": [r3(lo[0]), r3(hi[0])], "board_y": [r3(lo[1]), r3(hi[1])],
               "board_z": [r3(lo[2]), r3(hi[2])], "thickness": r3(hi[0] - lo[0])}
        for key in FRAMES:
            # groove = the wall pair (normal +X low wall, -X high wall) around the board
            lw = max((w for w in walls[key] if w[1] == 1 and w[0] <= lo[0] + 1e-6), key=lambda w: w[0])
            hw = min((w for w in walls[key] if w[1] == -1 and w[0] >= hi[0] - 1e-6), key=lambda w: w[0])
            fl = [f for f in floors[key] if lw[0] < f[2][0] < hw[0]][0]
            gl = fl[3] / (hw[0] - lw[0])  # groove length along y
            gy = (fl[2][1] - gl / 2, fl[2][1] + gl / 2)
            if key == "bottom":
                floor_gap = lo[2] - fl[0]
                engage = (lw[2][2] + (lw[3] / gl) / 2) - lo[2]
            else:
                floor_gap = fl[0] - hi[2]
                engage = hi[2] - (lw[2][2] - (lw[3] / gl) / 2)
            g = {"walls_x": [r3(lw[0]), r3(hw[0])], "groove_width": r3(hw[0] - lw[0]),
                 "groove_centre_x": r3((lw[0] + hw[0]) / 2),
                 "board_centre_offset": r3((lo[0] + hi[0]) / 2 - (lw[0] + hw[0]) / 2),
                 "clear_low": r3(lo[0] - lw[0]), "clear_high": r3(hw[0] - hi[0]),
                 "floor_z": r3(fl[0]), "floor_gap": r3(floor_gap), "engagement": r3(engage),
                 "groove_y": [r3(gy[0]), r3(gy[1])],
                 "board_inside_groove_y": gy[0] <= lo[1] and hi[1] <= gy[1]}
            g["pass"] = (g["clear_low"] > 0 and g["clear_high"] > 0 and g["floor_gap"] >= 0
                         and g["engagement"] > 0 and g["board_inside_groove_y"])
            row[key] = g
            ok = ok and g["pass"]
        rows.append(row)
    return {"status": "pass" if ok else "fail", "modules": rows}


def _pins(topo, dx=0.0):
    """Header pins between housing top and taper: [(x0, x1, z0, z1)]."""
    yl = (-48.8, -44.5)
    xs = intervals(planes(topo, 0, ylim=yl, area=(1, 5)), -1)
    zs = intervals(planes(topo, 2, ylim=yl, area=(1, 5)), -1)
    return [(a + dx, b + dx, c, d) for a, b in xs for c, d in zs]


def _cavities(topo):
    yl = (-48.8, -42.5)
    xs = intervals(planes(topo, 0, ylim=yl, area=(1, 8), zlim=(40, 70)), 1)
    zs = intervals(planes(topo, 2, ylim=yl, area=(1, 8)), 1)
    return [(a, b, c, d) for a, b in xs for c, d in zs]


def check_connectors(props, sc, overlaps):
    """B: module socket vs BusBoard header, per slot."""
    headers = [b for b in props["BusBoard"]["bodies"] if b["name"].startswith("PCN10-20P")]
    htopo = sc.call("body_topology", {"body": "PCN10-20P-2.54DSA"})
    # which instance did the name resolve to? the one whose bbox holds its pins
    p0 = _pins(htopo)
    ref = next(h for h in headers if bbox(h)[0][0] <= p0[0][0] <= bbox(h)[1][0])
    housing_top = max(planes(htopo, 1, sign=1), key=lambda f: f[3])[0]
    rows, worst = [], "pass"
    for m in MODULES:
        xb = HEADER_B_X[m]
        hdr = next(h for h in headers if bbox(h)[0][0] < xb < bbox(h)[1][0])
        dx = bbox(hdr)[0][0] - bbox(ref)[0][0]
        sock = next(b for b in props[m]["bodies"] if b["name"].startswith("PCN10C-20S"))
        stopo = sc.call("body_topology", {"body": sock["name"]})
        pins, cavs = _pins(htopo, dx), _cavities(stopo)
        per = []
        for p in pins:
            pc = ((p[0] + p[1]) / 2, (p[2] + p[3]) / 2)
            hits = [c for c in cavs if c[0] < pc[0] < c[1] and c[2] < pc[1] < c[3]]
            # the cavity is the tightest wall pair around the pin
            c = min(hits, key=lambda c: (c[1] - c[0]) * (c[3] - c[2])) if hits else None
            if c is None:
                per.append(None)
                continue
            per.append({"pin_xz": [r3(pc[0]), r3(pc[1])],
                        "dx": pc[0] - (c[0] + c[1]) / 2, "dz": pc[1] - (c[2] + c[3]) / 2,
                        "gap": min(p[0] - c[0], c[1] - p[1], p[2] - c[2], c[3] - p[3])})
        found = [q for q in per if q]
        smin, _ = bbox(sock)
        stop = max((f for f in planes(stopo, 1, sign=-1, area=(50, 1e9))
                    if f[0] > smin[1] + 1), key=lambda f: f[3])[0]
        ov = [o for o in overlaps if {o["occ_a"], o["occ_b"]} == {"BusBoard", m}
              and "PCN10C" in o["a"] + o["b"] and "PCN10-20P" in o["a"] + o["b"]]
        interf = bbox(hdr)[1][1] - stop
        row = {"module": m, "header_b_row_x": xb, "socket": sock["name"],
               "pins_found": len(pins), "pins_in_cavity": len(found),
               "max_abs_dx": r3(max(abs(q["dx"]) for q in found)) if found else None,
               "max_abs_dz": r3(max(abs(q["dz"]) for q in found)) if found else None,
               "min_side_gap": r3(min(q["gap"] for q in found)) if found else None,
               "socket_face_y": r3(smin[1]), "header_housing_top_y": r3(housing_top),
               "mating_face_gap": r3(smin[1] - housing_top),
               "header_top_y": r3(bbox(hdr)[1][1]), "socket_stop_y": r3(stop),
               "axial_interference": r3(interf),
               "overlap_mm3": r3(sum(o["volume_mm3"] for o in ov))}
        ok = (len(pins) == 20 and len(found) == 20 and row["min_side_gap"] > 0
              and row["max_abs_dx"] <= PIN_TOL and row["max_abs_dz"] <= PIN_TOL
              and abs(row["mating_face_gap"]) <= MATE_TOL and interf <= MATE_TOL)
        warn = row["overlap_mm3"] > COLLISION_MM3 or interf > 0.001
        row["status"] = "fail" if not ok else ("warn" if warn else "pass")
        if row["status"] == "fail" or (row["status"] == "warn" and worst == "pass"):
            worst = row["status"]
        rows.append(row)
    return {"status": worst, "slots": rows}


def check_holes(topo, props):
    """C: BusBoard holes vs back pockets; also plates and strips vs bores."""
    pockets = []
    for f in FRAMES.values():
        pockets += [c for c in cylinders(topo[f], 2.5)
                    if abs(abs(c["axis"][1]) - 1) < 1e-6 and abs(c["origin"][1] + 54) < 1e-3]
    pockets = axis_points(pockets, 1)
    bus = axis_points(cylinders(topo["BusBoard_PCB"], 1.6), 1)
    bus_m = match(bus, pockets)
    res = {"busboard_vs_pockets": {
        "holes": len(bus), "pockets": len(pockets),
        "max_offset": r3(max(o for _, _, o in bus_m)),
        "pairs": [{"hole_xz": [r3(v) for v in h], "pocket_xz": [r3(v) for v in t], "offset": r3(o)}
                  for h, t, o in sorted(bus_m)]}}
    b = res["busboard_vs_pockets"]
    b["status"] = "pass" if b["holes"] == 12 and b["max_offset"] <= HOLE_TOL else "fail"
    lo, hi = bbox(next(x for x in props["BusBoard"]["bodies"] if x["name"] == "BusBoard_PCB"))
    b["board_y"] = [r3(lo[1]), r3(hi[1])]
    b["gap_to_back_face_y-54"] = r3(-54.0 - hi[1])

    # other hole patterns (not one of the three questions; Q2-Q4 of assembly.md)
    side = []
    front = []
    for f in FRAMES.values():
        side += [c for c in cylinders(topo[f], 1.6) if abs(abs(c["axis"][0]) - 1) < 1e-6]
        front += [c for c in cylinders(topo[f], 1.6)
                  if abs(abs(c["axis"][1]) - 1) < 1e-6 and c["origin"][1] > 0]
    side_x = {}
    for c in side:
        side_x.setdefault("left" if c["origin"][0] < 0 else "right", []).append(c)
    extra = {}
    for occ, body, key in (("Deckplatte-links", "deckplatte", "left"),
                           ("Deckplatte-rechts", "deckplatte (2)", "right")):
        m = match(axis_points(cylinders(topo[body], 1.6), 0), axis_points(side_x[key], 0))
        extra[occ] = [{"hole_yz": [r3(v) for v in h], "bore_yz": [r3(v) for v in t], "offset": r3(o)}
                      for h, t, o in m]
    for occ, body in (("Leiste-1", "leiste"), ("Leiste-2", "leiste (2)")):
        m = match(axis_points(cylinders(topo[body], 1.6), 1), axis_points(front, 1))
        extra[occ] = [{"hole_xz": [r3(v) for v in h], "bore_xz": [r3(v) for v in t], "offset": r3(o)}
                      for h, t, o in m]
    for occ, body in (("Leiste-3", "leiste (3)"), ("Leiste-4", "leiste (4)")):
        m = match(axis_points(cylinders(topo[body], 1.6), 1), bus)
        extra[occ] = [{"hole_xz": [r3(v) for v in h], "busboard_hole_xz": [r3(v) for v in t],
                       "offset": r3(o)} for h, t, o in m]
    res["other_hole_patterns"] = extra
    return res


def owner(name, by_name):
    """Top-level occurrence of a body name as inspect.clearance reports it."""
    m = re.search(r"\(([^():/]+):\d+/", name)
    if m:
        return m.group(1)
    occ = by_name.get(name)
    return sorted(occ)[0] if occ else "?"


def collisions(sc, props, log):
    by_name = {}
    for o, p in props.items():
        for b in p["bodies"]:
            by_name.setdefault(b["name"], set()).add(o)
    t = time.time()
    r = execute(sc, "inspect.clearance",
                {"skip_within": "component", "clearance": 0.2, "min_volume": COLLISION_MM3}, log)
    secs = time.time() - t
    ov, touch, near = [], [], []
    for o in r.get("overlaps", []):
        a, b = owner(o["a"], by_name), owner(o["b"], by_name)
        if a == b:
            continue
        ov.append({"a": o["a"], "b": o["b"], "occ_a": a, "occ_b": b,
                   "volume_mm3": round(o["volume_mm3"], 4),
                   "bbox": [[r3(v) for v in o["bbox"]["min"]], [r3(v) for v in o["bbox"]["max"]]],
                   "center": [r3(v) for v in o["center"]]})
    for o in r.get("near", []):
        a, b = owner(o["a"], by_name), owner(o["b"], by_name)
        if a == b:
            continue
        e = {"a": o["a"], "b": o["b"], "occ_a": a, "occ_b": b,
             "distance_mm": r3(o["distance_mm"]), "at": [r3(v) for v in o["from"]]}
        if o.get("overlap_mm3") is not None:
            e["overlap_mm3"] = o["overlap_mm3"]
        (touch if o["distance_mm"] <= 1e-6 else near).append(e)
    return {"seconds": round(secs, 1), "bodies": r.get("bodies"),
            "pairs_checked": r.get("pairs_checked"), "pairs_pruned": r.get("pairs_pruned"),
            "unchecked": r.get("unchecked", []), "collisions": ov, "touching": touch,
            "near_under_0.2mm": near}


def images(sc):
    os.makedirs(IMG, exist_ok=True)
    out = {}
    execute(sc, "inspect.section", {"clear": True})
    # SolidCraft yaw 0 looks along +Y; the station's front (open side) is +Y,
    # so the front iso looks along -Y: yaw ~ pi, from front-left-above.
    out["iso_front"] = screenshot(sc, "station-front-iso.png", width=1400, height=1000,
                                  camera={"target": [0, 0, 55], "yaw": math.pi - 0.75,
                                          "pitch": 0.5, "distance": 290})
    out["right_side"] = screenshot(sc, "station-right-side.png", width=1000, height=900,
                                   camera={"target": [0, 0, 55], "yaw": -math.pi / 2,
                                           "pitch": 0.0, "distance": 330})
    execute(sc, "inspect.section", {"plane": "XZ", "at": 0})
    out["section_xz_y0"] = screenshot(sc, "section-slot2-grooves.png", width=1400, height=1100,
                                      camera={"target": [0, 0, 55], "yaw": math.pi,
                                              "pitch": 0.0, "distance": 235})
    execute(sc, "inspect.section", {"plane": "XY", "at": 56.27})
    out["section_xy_connector"] = screenshot(sc, "section-slot2-connector.png", width=1000, height=800,
                                             camera={"target": [-32, -46, 56], "yaw": 0,
                                                     "pitch": math.pi / 2 - 1e-4, "distance": 24})
    # through the b row of slot 2's header (x = -30): the 10 b pins in the socket
    execute(sc, "inspect.section", {"plane": "YZ", "at": HEADER_B_X["Slot2-CM4Carrier"]})
    out["section_yz_pinrow"] = screenshot(sc, "section-slot2-pinrow.png", width=1000, height=1000,
                                          camera={"target": [-30, -46, 55], "yaw": -math.pi / 2,
                                                  "pitch": 0.0, "distance": 45})
    execute(sc, "inspect.section", {"clear": True})
    return out


# ---------------------------------------------------------------- main

def main(argv):
    out_json = os.path.join(ROOT, "reference", "fit-check.json")
    if "--json" in argv:
        out_json = argv[argv.index("--json") + 1]
    log = lambda s: print(s, file=sys.stderr, flush=True)  # noqa: E731
    try:
        sc = SolidCraft(allow_paths=[ROOT])
    except OSError as e:
        print(f"cannot start solidcraft-cli: {e}")
        return 2
    try:
        ensure_station(sc)
        log("occurrence properties")
        props = {o: execute(sc, "occurrence.properties", {"occurrence": o + ":1"}) for o in OCCS}
        names = ["Grundgestell", "Grundgestell-gespiegelt", "deckplatte", "deckplatte (2)",
                 "leiste", "leiste (2)", "leiste (3)", "leiste (4)", "BusBoard_PCB"]
        topo = {n: sc.call("body_topology", {"body": n}) for n in names}
        log("interference / clearance over all bodies (takes minutes)")
        col = collisions(sc, props, log)
        log("checks")
        result = {
            "design": "desktop/station.sc",
            "thresholds": {"collision_mm3": COLLISION_MM3, "hole_offset": HOLE_TOL,
                           "pin_offset": PIN_TOL, "mating": MATE_TOL},
            "A_groove": check_grooves(props, topo),
            "B_connector": check_connectors(props, sc, col["collisions"]),
            "C_holes": check_holes(topo, props),
            "interference": col,
        }
        if "--no-images" not in argv:
            log("screenshots")
            result["images"] = images(sc)
        if sc.inspect().get("dirty"):
            result["warning"] = "design became dirty during the check"
    except SolidCraftError as e:
        print(f"ERROR {e}")
        return 2
    finally:
        sc.close()
    result["C_holes"]["status"] = result["C_holes"]["busboard_vs_pockets"]["status"]
    with open(out_json, "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")
    a, b, c = (result[k]["status"] for k in ("A_groove", "B_connector", "C_holes"))
    print(f"A groove      {a.upper()}")
    print(f"B connector   {b.upper()}")
    print(f"C holes       {c.upper()}")
    print(f"collisions (> {COLLISION_MM3} mm^3): {len(col['collisions'])}, "
          f"touching pairs: {len(col['touching'])}, near < 0.2 mm: {len(col['near_under_0.2mm'])}")
    for o in col["collisions"]:
        print(f"  {o['occ_a']} / {o['occ_b']}: {o['a']} x {o['b']} {o['volume_mm3']} mm^3")
    print(f"wrote {os.path.relpath(out_json, ROOT)}")
    return 0 if "fail" not in (a, b, c) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
