# Station assembly placement (derivation)

Input for `station.sc` (next task). Nothing here was built; all numbers are derived from the
part files (`desktop/parts/*.sc`, read from the `document.json` inside the archives, no app
interaction) and from the KiCad boards at the commits listed in `pcb/SOURCES.md`.

**Assembly frame:** origin = centre of the bottom frame's underside, +X along the 136 mm frame
length, +Y to the front (open groove side), +Z up. All lengths in mm.

**Transform convention:** each occurrence is first rotated about the part's own origin by the
listed rotations **in the listed order, each about the fixed assembly axes** (extrinsic), then
translated by `[x, y, z]`. `Rx(-90)` means -90 deg about X, right-hand rule.

## Open questions for Peter

1. **The cover plates are side plates (left/right), not front/back.** Their hole pattern only
   fits the side bores (x = ±68): plate columns z = 4.5/105.5 and 10/100 equal the frames'
   side bores at (y +55, z 4.5) and (y -49, z 10) of the bottom frame and z 105.5/100 of the
   top frame. No front/back face has bores at two different heights. The plate height 110 equals
   the stack height. The occurrences were therefore renamed (ruling R9) from the plan's
   `Deckplatte-vorne`/`-hinten` to `Deckplatte-links` (-X) and `Deckplatte-rechts` (+X). Still open:
   the spec says "vorne/hinten". **Peter to confirm the side placement.**
2. **One plate hole is 1.0 mm off.** Hole spacing from the plate's left column to its right
   column is 104 (bottom hole, x 8 to 112) and 103 (top hole, x 9 to 112). The side bores are
   104 apart (y +55 to -49) in **both** frames. With 3 holes on target (residual 0.000), the 4th
   (corner (9 | 105.5)) lands at y = 54.0 instead of 55.0 (residual 1.000 > 0.3). Least squares
   would give 0.25/0.75/0.25/0.25 (still > 0.3). Either the reconstructed hole (9 | 105.5) should be
   (8 | 105.5), or the real top frame's front side bores sit at y = 54. Which is it?
3. **Logo upside down on one side.** The plate pattern is not symmetric. With the logo outward
   and upright, it fits only the -X side. On +X the plate must be rotated 180 deg about its
   normal, so the logo stands upside down there. Do you want a mirrored plate for the right side?
4. **Where do the 4 strips go?** Two are certain: the front of each frame (holes x = ±50 match
   the front bores, z 4.5/105.5, residual 0.000). Nothing else on the frames has a 100 mm 2-hole
   pattern except the outer back pockets x = ±50 (z 10/100). This derivation therefore puts
   strips 3/4 on the back of the BusBoard as clamping bars (screw through strip and BusBoard
   holes H101/H106 resp. H109/H108 into the pockets). No back-side part of the BusBoard lies in
   the strip band. **UNVERIFIED hypothesis.** Is that how they are used?
5. Minor: **the module position comes from the connector, not the groove.** It sits 0.318 off
   the groove centre (inside the groove's ±0.70 play, see E5). It stands 0.5 above both groove
   floors and rests on the connector. Socket opening heights (2.98/5.52 above the board) and the
   header housing height (5.2) are read from the vendor STEP models in the module repos, not
   from a datasheet.
6. Convention, not a question: the stack is symmetric under a 180 deg turn about Y (normal frame
   bottom equals mirrored frame bottom turned over). As the plan says, the normal frame is at
   the bottom. That puts the PowerBoard at -X (right when seen from the front).

## Summary

- Stack height **110**: bottom frame (`grundgestell`, z 0…20) plus top frame
  (`grundgestell-gespiegelt` turned 180 deg about Y, z 90…110). This is fixed by the BusBoard's
  hole rows (90 apart, 5 from its edges) on the back pockets at z 10/100 (residual 0.000 on all
  12 holes). The BusBoard edges then sit exactly on both 5 mm back steps.
- BusBoard: F.Cu (connectors) faces +Y and lies flat on the back faces y = -54. Slot connectors run
  from J301 (PowerBoard) at x = -50 through J201 (CM4) at -30 to J401…J701 (FM 1–4) at -10, +10, +30, +50.
- Modules stand in the YZ plane, component side to +X, front edge (XT60/RJ45/SMA) at +Y. The
  back edge is at y = -42.374, 0.126 in front of the back wall. Module pin k mates header pin 11-k (net-checked),
  same row letter. Pin rows match to 0.000 in X/Z.
- Side plates and front strips: residual 0.000, except one plate hole at 1.000 (question 2).
- Status: **11 VERIFIED, 4 UNVERIFIED** (2 cover plates, 2 back strips).

## Occurrence table

| # | name | source file | translation [x, y, z] | rotation (ordered) | status | evidence |
|---|---|---|---|---|---|---|
| 1 | Gestell | `desktop/parts/grundgestell.sc` | [0, 0, 0] | none | VERIFIED | E1, E2 |
| 2 | Gestell-gespiegelt | `desktop/parts/grundgestell-gespiegelt.sc` | [0, 0, 110] | Ry(180) | VERIFIED | E1, E2 |
| 3 | Deckplatte-links (**left, -X**, logo upright; spec: "vorne") | `desktop/parts/deckplatte.sc` | [-68, 4.5, 55] | Rx(90), Rz(-90) | UNVERIFIED | E6, Q1–3 |
| 4 | Deckplatte-rechts (**right, +X**, logo upside down; spec: "hinten") | `desktop/parts/deckplatte.sc` | [68, 4.5, 55] | Rx(-90), Rz(-90) | UNVERIFIED | E6, Q1–3 |
| 5 | Leiste-1 (front, bottom frame) | `desktop/parts/leiste.sc` | [0, 60, 4.25] | Rx(-90) | VERIFIED | E7 |
| 6 | Leiste-2 (front, top frame) | `desktop/parts/leiste.sc` | [0, 60, 105.75] | Rx(-90), Ry(180) | VERIFIED | E7 |
| 7 | Leiste-3 (back, bottom, over BusBoard) | `desktop/parts/leiste.sc` | [0, -55.6012, 9.75] | Rx(-90), Rz(180) | UNVERIFIED | E7, Q4 |
| 8 | Leiste-4 (back, top, over BusBoard) | `desktop/parts/leiste.sc` | [0, -55.6012, 100.25] | Rx(90) | UNVERIFIED | E7, Q4 |
| 9 | BusBoard | `pcb/BusBoard.step` | [-125.284, -55.6012, -20.396] | Rx(-90) | VERIFIED | E3, E4, E8 |
| 10 | Slot1-PowerBoard | `pcb/PowerBoard.step` | [-57.1212, 157.194, -35.64] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |
| 11 | Slot2-CM4Carrier | `pcb/CM4Carrier.step` | [-37.1212, 150.848, -40.794] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |
| 12 | Slot3-FMTransceiver | `pcb/FMTransceiver.step` | [-17.1212, 155.543, -31.271] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |
| 13 | Slot4-FMTransceiver | `pcb/FMTransceiver.step` | [2.8788, 155.543, -31.271] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |
| 14 | Slot5-FMTransceiver | `pcb/FMTransceiver.step` | [22.8788, 155.543, -31.271] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |
| 15 | Slot6-FMTransceiver | `pcb/FMTransceiver.step` | [42.8788, 155.543, -31.271] | Rx(-90), Rz(-90) | VERIFIED | E5, E8 |

15 occurrences, matching ruling R4. Resulting axis maps (part-local → assembly):

| occurrence | local x → | local y → | local z → |
|---|---|---|---|
| Gestell | +X | +Y | +Z |
| Gestell-gespiegelt | -X | +Y | -Z |
| Deckplatte-links | -Y | +Z | -X (logo outward) |
| Deckplatte-rechts | -Y | -Z | +X (logo outward) |
| Leiste-1 | +X | -Z | +Y |
| Leiste-2 | -X | +Z | +Y |
| Leiste-3 | -X | -Z | -Y |
| Leiste-4 | +X | +Z | -Y |
| BusBoard (STEP) | +X | -Z | +Y (F.Cu side) |
| modules (STEP) | -Y | -Z | +X (F.Cu side) |

Resulting extents (checked by transforming the corners):

| occurrence | x | y | z |
|---|---|---|---|
| Gestell | -68…68 | -60…60 | 0…20 |
| Gestell-gespiegelt | -68…68 | -60…60 | 90…110 |
| Deckplatte left / right | -71.6…-68 / 68…71.6 (incl. 0.6 logo) | -54…63 | 0…110 |
| Leiste-1 / -2 | -68…68 | 60…63 | 0…8.5 / 101.5…110 |
| Leiste-3 / -4 | -68…68 | -58.601…-55.601 | 5.5…14 / 96…104.5 |
| BusBoard (board) | -60…57.366 | -55.601…-54.000 | 5…105 |
| module boards | X_c ± 0.80 | -42.374…57.626 | 5…105 |

Board centre planes X_c: PowerBoard -56.318, CM4 -36.318, FM -16.318 / 3.682 / 23.682 / 43.682.

## Evidence

### E1 Frames (from `document.json` of both `.sc` files)

Parameters are the same in both files: L 136, D 120, deck_h 8.5, wall 11.5 × 20, step 6 × 5, margin 8,
slot 10 × 92.5, pitch 20, groove_off 16, groove 3 wide × 4 deep, insert Ø5 × 5, screw Ø3.2.
`grundgestell-gespiegelt.sc` holds the original features. `grundgestell.sc` is the same plus
`Mirror1` about YZ and `Remove1` of the source body. Part origin = centre of underside, which is
the assembly origin for the bottom frame.

| feature (mirrored file) | value | normal file (x mirrored) |
|---|---|---|
| slots (Durchbrueche) | x -60+20i … -50+20i, y -42.5…50 | x 50-20i … 60-20i |
| grooves (Nuten), centres | x -44+20i, z 4.5…8.5, y -42.5…61 (open front) | x 44-20i |
| back pockets Ø5 × 5 | x -50+20i, y -54 → +Y, z 10 | same (symmetric) |
| side bores Ø5×5 + Ø3.2 to 10 | x = ±68, (y -49, z 10) and (y 55, z 4.5) | same |
| front bores Ø5×5 + Ø3.2 to 9 | y 60, x ±50, z 4.5 | same |

Top frame = mirrored file under Ry(180) + z 110. Its features in assembly coordinates:
grooves x = 44, 24, 4, -16, -36, -56 (identical to the bottom frame's grooves, residual 0.000),
groove floor z 105.5, pockets z 100, side bores (y -49, z 100) and (y 55, z 105.5), front bores
(x ±50, y 60, z 105.5), back step z 105…110 at y -60…-54. The mirrored frame exists exactly so
that it lines up with the normal frame when turned over.

### E2 Stack height 110

| constraint | gives H |
|---|---|
| BusBoard hole rows 90 apart (y 30.396 / 120.396) on pockets at z 10 and H-10 | 110.000 |
| BusBoard 100 tall, holes 5 from the edges → edges at z 5 / 105 = bottom step top (5) and top step face (H-5) | 110.000 |
| plate height 110 = H; plate hole columns 4.5/105.5 and 10/100 = side bores 4.5/H-4.5, 10/H-10 | 110.000 |
| groove floors 4.5 / H-4.5 = 4.5 / 105.5 → 101 gap for a 100 board (0.5 clearance each side) | consistent |

### E3 BusBoard (`BusBoard.kicad_pcb` @ d8b12e2)

- Edge.Cuts gr_rect (65.284, 25.396)–(182.650, 125.396) → 117.366 × 100.000.
- 12 × `MountingHole_3.2mm_M3`: x = 75.284 + 20i (i = 0…5), y = 30.396 (H101–H106) and 120.396
  (H109, H110, H111, H112, H107, H108 from left to right). Hole pattern centre x 125.284. Edge distances: 10.000 left and 7.366 right,
  5.000 top and bottom.
- 6 × `PCN10-20P-2.54DSA` (straight 2 × 10 pin header, F.Cu, rot 180). For each one the b row
  is at the hole x and the a row at x - 2.54. Pins 1…10 run y 86.826 → 63.966. Pegs Ø2.85 sit at
  y 94.446 / 56.346.

| ref | role (doc/index.md, nets) | KiCad b1 x | assembly b-row x | a1 (x, y, z) | a10 (x, y, z) |
|---|---|---|---|---|---|
| J301 | Power connector → **Slot 1 PowerBoard** | 75.284 | -50 | (-52.54, -54, 66.43) | (-52.54, -54, 43.57) |
| J201 | RPI/CM4 connector → **Slot 2 CM4Carrier** | 95.284 | -30 | (-32.54, -54, 66.43) | (-32.54, -54, 43.57) |
| J401 | Device slot 1 → Slot 3 FM | 115.284 | -10 | (-12.54, -54, 66.43) | (-12.54, -54, 43.57) |
| J501 | Device slot 2 → Slot 4 FM | 135.284 | +10 | (7.46, -54, 66.43) | (7.46, -54, 43.57) |
| J601 | Device slot 3 → Slot 5 FM | 155.284 | +30 | (27.46, -54, 66.43) | (27.46, -54, 43.57) |
| J701 | Device slot 4 → Slot 6 FM | 175.284 | +50 | (47.46, -54, 66.43) | (47.46, -54, 43.57) |

Header nets: a1/b1 GND, a2/a3 I²C (J201/J301 only), a5/b5 USB±, a6/a7/b6/b7 +5V, a8/b8 GND,
a9/a10/b9/b10 +12V.

The holes go on the back pockets. KiCad (u, v) → assembly X = u - 125.284, Z = v - 20.396,
F.Cu plane at y = -54.

| hole | assembly (x, y, z) | pocket | residual |
|---|---|---|---|
| H101…H106 (v 30.396) | (-50…+50 step 20, -54, 10) | bottom pockets x -50+20i | 0.000 (all 6) |
| H109, H110, H111, H112, H107, H108 (v 120.396; x -50…+50 step 20) | (-50…+50 step 20, -54, 100) | top pockets | 0.000 (all 6) |

Board extents: x -60.000…57.366, z 5…105. The 1.317 off-centre of the hole pattern is to -X.
Nothing on F.Cu besides the mounting holes lies in the wall bands (z < 20 or z > 90), so the
board can lie flat on the wall faces. Back-side (B.Cu) parts lie at KiCad y 84…110, i.e. z 64…90.
That is clear of the back strips' bands z 5.5…14 and 96…104.5.

The in-plane orientation (u → +X rather than -X) is decided by E5: only this orientation mates
pin 1 correctly *and* matches the socket row heights. The 180-deg alternative puts GND on +12V
(Z mismatch of 22.86) and misses the rows by 2.22.

### E4 BusBoard Y position

The back face of the back wall is at y = -54 (`Profil` p6/p7). The F.Cu side lies on it, so the
board occupies y -55.601…-54.000, inside the 6-deep step (y -60…-54). It stands on the bottom
step (z 5) and touches the top frame's step face (z 105). Heat-set inserts (Ø5 × 5 pockets,
interpretation per spec) take M3 screws from the back through the BusBoard holes.

### E5 Modules (PowerBoard @ 84e5044, CM4Carrier @ 452df89, FMTransceiver origin/main @ 30d8ed2)

| board | Edge.Cuts rect | socket ref (`PCN10C-20S-2.54DS`, rot -90) | a1 pad | a10 pad | M3 holes |
|---|---|---|---|---|---|
| PowerBoard | (99.568, 40.640)–(199.568, 140.640) | J102 | (193.294, 79.210) | (193.294, 102.070) | (104.568, 48.140), (104.568, 133.140) |
| CM4Carrier | (93.222, 45.794)–(193.222, 145.794) | J101 | (186.948, 84.364) | (186.948, 107.224) | (98.222, 53.294), (98.222, 138.294) |
| FMTransceiver | (97.917, 36.271)–(197.917, 136.271) | J202 | (191.643, 74.841) | (191.643, 97.701) | (102.917, 43.771), (102.917, 128.771) |

All boards are 100.000 × 100.000. The socket sits identically on all three: a row 6.274 from the
right edge (u_max), b row 2.54 further in, a1 38.570 below the top edge. Front parts (XT60 J101,
RJ45 J301, SMA J101) sit at the left edge → KiCad u_min = front (+Y), u_max = back.

Socket nets (all three): a1/a2/b1 +12V, a3 GND, a5/b5 +5V, a6 USB+, a8/a9 I²C (PB, CM4), a10/b10 GND.
Against the header: module pin k ↔ header pin 11-k, same letter (a1 12V ↔ a10 12V,
a6 USB+ ↔ a5 USB+, a9 SCL ↔ a2 SCL, a10 GND ↔ a1 GND). So the module's a1 must sit at the
header's a10 height, z 43.57.

Socket geometry from `3d-models/PCN10C-20S-2.54DS.stp` placed as in the footprint (offset
(-71.7, 1.2, 8.3), rot x 90). Placement origin in `pcb/PowerBoard.step` = (194.494, -7.51, 9.9012):
- mating face 11.5 in front of the model origin → 6.426 beyond the board's back edge;
- 2 openings (1.80 tall) centred **2.98** (a, edge row) and **5.52** (b) above the board's top face.

Header geometry from `3d-models/PCN10-20P-2.54DSA.stp`: housing top 5.2 above the BusBoard
(728 vertices at z 5.2), pin tips up to 11.6.

Module placement derivation (component side +X, i.e. facing the header):
- X: b opening at the header b row → top face at X_b - 5.52, board centre X_b - 6.318. The a
  opening lands at X_b - 2.54 = the header a row, residual 0.000.
- Z: a1 at z 43.57 → top edge at z 5.000, bottom edge at 105.000 (0.5 above both groove floors).
- Y: socket face on the header housing → face at y = -54 + 5.2 = -48.8, back edge at
  -48.8 + 6.426 = **-42.374**. The back wall's front face is at -42.5, so 0.126 clearance.
  Front edge at 57.626, 2.374 behind the frame front (y 60).

| slot | header X_b | board centre X_c | groove centre | X_c - groove | board faces x | groove walls x |
|---|---|---|---|---|---|---|
| 1 PowerBoard | -50 | -56.318 | -56 | -0.318 | -57.121 / -55.520 | -57.5 / -54.5 |
| 2 CM4Carrier | -30 | -36.318 | -36 | -0.318 | -37.121 / -35.520 | -37.5 / -34.5 |
| 3 FM | -10 | -16.318 | -16 | -0.318 | -17.121 / -15.520 | -17.5 / -14.5 |
| 4 FM | +10 | 3.682 | 4 | -0.318 | 2.879 / 4.480 | 2.5 / 5.5 |
| 5 FM | +30 | 23.682 | 24 | -0.318 | 22.879 / 24.480 | 22.5 / 25.5 |
| 6 FM | +50 | 43.682 | 44 | -0.318 | 42.879 / 44.480 | 42.5 / 45.5 |

The board (1.606 thick) fits in the 3.0 groove with 0.379 / 1.020 to the walls. The 0.318 is a
position inside a clearance fit, not a hole-pattern residual, so modules are VERIFIED.

Translation formula for a module STEP (KiCad edge rect u0…u1, v0…v1; top face z_s = 1.6012):
`t = [X_b - (1.6012 + 5.52), -42.374 + u1, 5.0 - v0]` with rotation Rx(-90), Rz(-90), which maps
STEP (x, y, z) → (z, -x, -y).

The modules' own M3 holes (5 from the front edge, 7.5 from top/bottom) land at y 52.626,
z 12.5 / 97.5. They match no frame feature and are probably for module front panels.

### E6 Cover plates (`deckplatte.sc`: W 117 along local x, H 110 along local y, T 3, logo +0.6 on +z)

Holes in plate-local coordinates (corner (-58.5, -55) + offsets): A (8 | 4.5) = (-50.5, -50.5),
B (9 | 105.5) = (-49.5, 50.5), C (112 | 10) = (53.5, -45), D (112 | 100) = (53.5, 45).

| plate | A | B | C | D |
|---|---|---|---|---|
| left (-X) | (-68, 55, 4.5) → side bore (55, 4.5) **0.000** | (-68, 54.0, 105.5) → (55, 105.5) **1.000** | (-68, -49, 10) **0.000** | (-68, -49, 100) **0.000** |
| right (+X) | (68, 55, 105.5) **0.000** | (68, 54.0, 4.5) → (55, 4.5) **1.000** | (68, -49, 100) **0.000** | (68, -49, 10) **0.000** |

Plate extents: y -54…63 (back edge flush with the frame's back wall face; front edge covers the
3 mm front strips), z 0…110. Front/back alternatives fail. The front face has only 2 bores, both
at z 4.5 (plate A/C heights differ: 4.5 vs 10). The back face has pockets only at z 10/100 and
none at 4.5/105.5.

### E7 Strips (`leiste.sc`: 136 along x, 8.5 along y (±4.25), 3 thick on +z; Ø3.2 at (±50, -0.25), i.e. 4.0 from the -y edge and 4.5 from the +y edge)

| strip | holes in assembly | target | residual | band |
|---|---|---|---|---|
| Leiste-1 front bottom | (±50, 60, 4.5) | front bores bottom frame (x ±50, y 60, z 4.5) | 0.000 | y 60…63, z 0…8.5 = deck front face |
| Leiste-2 front top | (±50, 60, 105.5) | front bores top frame | 0.000 | y 60…63, z 101.5…110 |
| Leiste-3 back bottom | (±50, -55.601, 10) | BusBoard H101/H106 → pockets (±50, -54, 10) | 0.000 | y -58.601…-55.601, z 5.5…14 |
| Leiste-4 back top | (±50, -55.601, 100) | BusBoard H109/H108 → pockets (±50, -54, 100) | 0.000 | y -58.601…-55.601, z 96…104.5 |

In each strip the 4.5 edge distance faces the frame's outer face (underside / top). The front
strips close the open groove ends (grooves run to y 61) and cover the deck's front faces. The
back strips are a hypothesis (Q4).

### E8 STEP origins (computed from the .kicad_pcb and the STEP text, not inserted in SolidCraft)

The app had `deckplatte` open (clean), and lock files for the other parts showed concurrent use,
so `file.insert_step` was not run. `pcb/export-steps.sh` calls `kicad-cli pcb export step
--subst-models` without an origin option. The STEP origin is therefore the **KiCad page origin
(0, 0)** of each `.kicad_pcb`: STEP x = KiCad x, STEP y = -KiCad y, STEP z = 0 at the board
underside. Component models sit on the top face at **z = 1.6012** (all placements, e.g. BusBoard
header origins (69.684, -51.226, 1.6012), PowerBoard socket (194.494, -7.51, 9.9012 = 1.6012 + 8.3)).
Board stack-up thickness 1.6062.

| STEP | board rect in STEP coords (x; y) | 
|---|---|
| BusBoard.step | 65.284…182.650; -125.396…-25.396 |
| PowerBoard.step | 99.568…199.568; -140.640…-40.640 |
| CM4Carrier.step | 93.222…193.222; -145.794…-45.794 |
| FMTransceiver.step | 97.917…197.917; -136.271…-36.271 |

Checks: PowerBoard.step vertex bbox reaches x 199.568 / y -140.64 (= board edge). BusBoard.step
reaches x 182.65 / y -125.396.

The DeviceTester (`DeviceTester*.step`) is not part of the station (it has a PCN10-20P header of
its own and its socket on the opposite edge).

## Screw map (what screws where)

| bore | count | joins |
|---|---|---|
| back pockets Ø5 × 5, x -50+20i, z 10 (bottom) / 100 (top) | 12 | BusBoard H101–H112 (M3 from the back, through the BusBoard; at x ±50 also through Leiste-3/-4) |
| side bores Ø5×5 + Ø3.2 at x ±68, (y -49, z 10/100), (y 55, z 4.5/105.5) | 8 | the 2 side plates, 4 screws each (holes C/D at the back, A/B at the front) |
| front bores Ø5×5 + Ø3.2 at (x ±50, y 60, z 4.5/105.5) | 4 | Leiste-1 and Leiste-2, 2 screws each |

The modules are not screwed. They are held by the grooves (both frames) and the bus connector.
