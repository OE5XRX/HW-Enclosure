# Station fit check

## Ergebnis

| Frage | Ergebnis | Kurz |
|---|---|---|
| (a) Passen die Module in die Kartennuten? | ✅ | Alle 6 Platinen stehen in beiden Rahmen in der Nut: 0,379 mm Luft auf der Rückseite, 1,020 mm auf der Bestückungsseite (bei 1,6 mm Platinendicke), 0,5 mm über dem Nutgrund, 3,5 mm Eingriff. Kein Bauteil eines Moduls berührt Gehäuse oder Nachbarmodul. |
| (b) Stecken die Modul-Busstecker auf den BusBoard-Steckern? | ⚠️ | In allen 6 Slots sitzen alle 20 Stifte in ihren Buchsenkammern (Versatz ≤ 0,03 mm in X, ≤ 0,09 mm in Z, mindestens 0,07 mm Luft je Seite). Die Steckflächen liegen exakt aufeinander (Spalt 0,000). Aber: Die beiden Herstellermodelle haben Anschlagebenen, die 0,10 mm auseinanderliegen; dadurch überschneiden sie sich um 4,129 mm³ je Slot (Befund 1, Ursache offen). Nach der Regel (> 0,01 mm³) ist das eine Kollision, daher ⚠️ und Exit-Code 1. |
| (c) Passen die BusBoard-Löcher auf die Taschen im Rahmen? | ✅ | Alle 12 Löcher liegen achsgleich auf den 12 Taschen (Versatz 0,000 mm). |

**Kollisionen:** 6, alle dieselbe Steckermodell-Überschneidung (Befund 1). Sonst gibt es keine Überschneidung zwischen Platinen, Bauteilen und Gehäuse.
**Außerhalb der drei Fragen:** Ein Deckplatten-Loch liegt bestätigt 1,000 mm daneben, an beiden Platten (Befund 2, offene Frage Q2). Das Logo rechts steht bestätigt auf dem Kopf (Befund 3, Q3). Die hinteren Leisten passen geometrisch (Q4, Befund 4).

Nichts wurde geändert. `desktop/station.sc` und alle Teile sind unverändert. Diese Datei berichtet nur.

![Station von vorne (iso)](img/station-front-iso.png)

*Iso-Ansicht von vorne (offene Seite +Y). Links SMA (FM 1–4), Mitte RJ45 (CM4), rechts XT60 (PowerBoard). Die sichtbare Seitenplatte ist Deckplatte-links (−X, im Bild rechts); ihr Logo steht aufrecht.*

![Schnitt y = 0 durch alle Slots](img/section-slot2-grooves.png)

*Schnitt XZ bei y = 0, Blick von vorne nach hinten. Slot 2 (CM4) ist die zweite Platine von rechts. Jede Platine steht oben und unten in der Nut: Luft links/rechts, 0,5 mm über dem Nutgrund. Hinten liegt das BusBoard (grün) mit den 6 Steckerpaaren.*

![Schnitt durch die Steckerstifte von Slot 2](img/section-slot2-connector.png)

*Schnitt XY bei z = 56,27 (Stiftpaar a6/b6 von J201) durch Slot 2, Blick von oben. Unten liegen das BusBoard und das Stiftgehäuse, darüber die Buchse mit den beiden Kammern, oben links die CM4-Platine (olivgrün). Die dünne Linie quer über die Buchse bei y = −42,5 … −42,4 ist die 0,1 mm dicke Überschneidung der beiden Modelle (Befund 1).*

![Schnitt durch die b-Reihe von Slot 2](img/section-slot2-pinrow.png)

*Schnitt YZ bei x = −30 (b-Reihe von J201), alle 10 b-Stifte in ihren Kammern.*

![Rechte Seite](img/station-right-side.png)

*Rechte Seite (+X). Das Logo der Deckplatte-rechts steht auf dem Kopf (Q3).*

## Method

`tools/fit_check.py` checks the open app (`solidcraft --control 7878`) through `tools/sc_mcp.py` and only reads the design:

- `occurrence.properties` for the 15 top-level occurrences gives the world bounding box of every placed body (665 bodies; instanced STEP sub-bodies included).
- `body_topology` gives exact faces in world coordinates: planar faces with normals, and cylinders with axis and radius. It is used for the frames, plates, strips, BusBoard PCB, one header instance and the 6 sockets.
- `inspect.clearance` (SolidCraft's interference/clearance command) runs over all 665 placed bodies with `skip_within: "component"`, `min_volume: 0.01` and `clearance: 0.2`. In a fresh app session the run took 453 s; 47 pairs were intersected exactly and 169 540 pruned by box/mesh (an exploratory run with `skip_within: "occurrence"`, which keeps the part-on-own-PCB pairs, intersected 776). Re-runs reuse the cached pairs (< 1 s); the committed `fit-check.json` is from such a cached re-run (`pairs_checked` 47, `pairs_reused` 47, `seconds` 0.9). It reported 0 unchecked pairs. Pairs inside one top-level occurrence (a part on its own PCB) are dropped.
- `inspect.section` plus `screenshot {source: "model", camera}` give the pictures. The section is cleared again at the end.

No scratch design was needed, because SolidCraft has a direct interference command. `station.sc` was never modified or saved: `dirty: false` before and after each run, and the app still shows `station`, clean.

Re-run: `python3 tools/fit_check.py` (add `--no-images` to skip the pictures). It writes `reference/fit-check.json`. Exit 0 = all three checks "pass", 1 = any check is "warn" or "fail" (currently 1, because B is "warn"), 2 = the app cannot be used (e.g. another design with unsaved changes is open).

Pass criteria: groove clearance > 0 on both sides, floor gap ≥ 0, engagement > 0. Connector: 20/20 pins inside a cavity, side gap > 0, pin-to-cavity centre offset ≤ 0.15, mating-face gap and axial interference ≤ 0.2. Holes: axis offset ≤ 0.1. A collision is an overlap > 0.01 mm³.

## (a) Board edge in the grooves

Groove walls and floors come from the frame faces (`body_topology`). Board extents come from the PCB body of each module.

| module | board x (underside … component plane) | groove walls x | clearance −X / +X | board centre − groove centre | floor gap bottom / top | engagement bottom / top | board y in groove y |
|---|---|---|---|---|---|---|---|
| Slot1 PowerBoard | −57.121 … −55.520 | −57.5 / −54.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | −42.374…57.626 in −42.5…60 |
| Slot2 CM4Carrier | −37.121 … −35.520 | −37.5 / −34.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | same |
| Slot3 FM | −17.121 … −15.520 | −17.5 / −14.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | same |
| Slot4 FM | 2.879 … 4.480 | 2.5 / 5.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | same |
| Slot5 FM | 22.879 … 24.480 | 22.5 / 25.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | same |
| Slot6 FM | 42.879 … 44.480 | 42.5 / 45.5 | 0.379 / 1.020 | −0.321 | 0.5 / 0.5 | 3.5 / 3.5 | same |

The top frame gives the same numbers as the bottom frame (floor z 105.5 vs board top 105.0).

This confirms assembly.md:
- Board thickness is taken as 1.6012 (underside to the component plane where every STEP component sits). The exported KiCad board *body* is only 1.516 thick (core without copper/mask), so measuring to the body face would give 1.105 / −0.363: that is a model artefact, not real clearance. The verdict values above (1.020, centre −0.321) match assembly.md's prediction (0.379 / 1.020, −0.318 for a 1.606 stack) to 0.003. The script records both (`clear_high`, `clear_high_body`).
- The back edge is 0.126 in front of the back wall's front face (y −42.5), in both frames. This is the closest the modules come to the enclosure.
- No module component overlaps, touches or comes within 0.2 mm of a frame, plate, strip or neighbouring module.

## (b) Connector mating

Per slot: header instance (on the BusBoard) vs the module's socket (`PCN10C-20S-2.54DS`). Pin side faces (0.6 × 0.6 pins) come from the header topology, translated to each instance. Cavity walls (0.8 × 1.1) come from each socket's own topology.

| slot | header b row x | pins in cavity | max \|dx\| | max \|dz\| | min side gap | socket face y / header housing top y | mating gap | header top y / socket stop y | axial interference | overlap |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 PowerBoard (J301) | −50 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |
| 2 CM4Carrier (J201) | −30 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |
| 3 FM 1 (J401) | −10 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |
| 4 FM 2 (J501) | +10 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |
| 5 FM 3 (J601) | +30 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |
| 6 FM 4 (J701) | +50 | 20/20 | 0.030 | 0.090 | 0.070 | −48.8 / −48.8 | 0.000 | −42.4 / −42.5 | 0.100 | 4.129 mm³ |

Pin positions are taken from the 3D models. The header pins sit at x −12.57/−10.03 for J401, i.e. 0.03 from the footprint rows −12.54/−10.00 (BusBoard holes, exact). In z they sit 0.02 above the footprint. The socket cavities sit exactly on the rows in x and 0.07 below the footprint in z. The 0.09 z offset therefore comes from two vendor-model offsets, not from the placement. The THT holes of the module sockets (PCB body) are at the header pin heights z 43.57 … 66.43, to 0.000.

## (c) BusBoard holes vs back pockets

Axes of the 12 Ø3.2 BusBoard holes (`BusBoard_PCB`) against the 12 Ø5 pocket axes in the back faces y = −54 of both frames:

| holes | x | z | offset |
|---|---|---|---|
| H101–H106 → bottom pockets | −50, −30, −10, 10, 30, 50 | 10 | 0.000 (all 6) |
| H109, H110, H111, H112, H107, H108 → top pockets | −50, −30, −10, 10, 30, 50 | 100 | 0.000 (all 6) |

The board edges rest on both 5 mm steps: contact at z 5 (bottom frame) and z 105 (top frame). The header housings sit at y −54.000 (housing top −48.8 = −54.000 + 5.2), i.e. the BusBoard's component side lies exactly on the back faces y −54. The `BusBoard_PCB` body face at y −54.085 is the same thin-body artefact as on the modules (Befund 5).

## Other hole patterns (not part of the three questions)

| occurrence | holes vs target | offsets |
|---|---|---|
| Deckplatte-links | 4 holes vs side bores (Ø3.2, x −63) | 0.000, **1.000** (y 54 vs 55, z 105.5), 0.000, 0.000 |
| Deckplatte-rechts | 4 holes vs side bores (x +63) | 0.000, **1.000** (y 54 vs 55, z 4.5), 0.000, 0.000 |
| Leiste-1 / Leiste-2 | 2 holes each vs front bores (y 55, x ±50) | 0.000 |
| Leiste-3 / Leiste-4 | 2 holes each vs BusBoard holes H101/H106, H109/H108 | 0.000 |

## Interference summary

- **Collisions (overlap > 0.01 mm³): 6.** Each is a module socket against its BusBoard header, 4.129 mm³, in the slab y −42.5 … −42.4, x ±4.05 around the connector, z 38.97 … 71.07 (Befund 1).
- **Touching (distance 0), 14 pairs, all intended contacts:** both frames with both plates, both frames with the front strip of their frame, both plates with both front strips, the BusBoard edges on the bottom step (z 5) and top step (z 105), Leiste-3/-4 on the back of the BusBoard.
- **Near (0 < d < 0.2 mm), 18 pairs:** each module PCB back edge is 0.026 from its header's top corner, and each module PCB is 0.126 from the back walls of both frames.
- PCB vs PCB: none. The only contact between boards is the connector pair.
- Unchecked pairs: 0 (there are no mesh bodies).

## Findings

1. **Connector models overlap 0.10 mm axially (all 6 slots, 4.129 mm³ each).** The socket's mating face lies exactly on the header housing (y −48.8; this is how assembly.md placed it). Behind that, the header model has a second seating plane at y −42.4 (11.6 above the BusBoard component plane) and the socket model one at y −42.5: two seating planes 0.10 mm apart. The overlap is 4.129 mm³ / 0.1 mm = 41.3 mm² over a bbox of 8.1 × 32.1 mm, i.e. housing-sized, not the pin tips (20 pins × 0.36 mm² = 7.2 mm² at most). The cause is unresolved: no datasheet mated height was checked. In reality one of two things happens. Either the header bottoms out in the socket 0.10 mm before the faces touch, so the module sits 0.10 mm further forward: back-wall clearance goes from 0.126 to 0.226 and the front edge to 57.726 (frame front 60). Or the two vendor models are not exact about the mated height. Neither case is a fit problem: the board stays in the grooves (3.5 mm engagement along z is unaffected) and the pins are inside the cavities. → ⚠️ instead of ✅ for (b).
2. **Cover plate hole 1.000 off (Q2, confirmed on both plates).** Hole B of the plate (local (9 | 105.5)) lands at y 54.0 while the bores are at y 55.0. It is at the top front corner on the left plate and the bottom front corner on the right plate. The Ø3.2 hole and the Ø3.2 bore overlap only in a 2.2 mm wide passage, so an M3 screw (3.0) will not go through without opening up the hole. Either the plate hole should be (8 | 105.5), or the frame bore is at y 54.
3. **Logo upside down on Deckplatte-rechts (Q3, confirmed).** See the right-side picture. The geometry proves it independently: the plate's 1.0-off hole B (local top) lies at the bottom (z 4.5) on the right plate and at the top (z 105.5) on the left plate, so the right plate is the same part turned 180° about its normal.
4. **Back strips Leiste-3/-4 (Q4).** Geometrically consistent: hole offset 0.000 to BusBoard H101/H106 and H109/H108 (and thus to the pockets), lying flat on the BusBoard's back face (contact), no overlap with anything. The header pin tails stick out to y −57.2 at z 33…77, far from the strip bands z 5.5…14 / 96…104.5. The strips are 0.5 from the frame steps (z 5 vs 5.5). Whether they are *meant* to be there is still Peter's call.
5. **Board body thickness is a model artefact, not a gap.** The KiCad STEP export makes every board body ~1.516 thick (core without copper/mask), while all components sit on the 1.6012 component plane. On the BusBoard the header bases are exactly at y −54.000 (on the back faces), so the real board lies flat on the frame; the 0.085 between `BusBoard_PCB` (y −54.085) and y −54 does not exist on the real part and nothing shifts when screwed. On the modules the same artefact would inflate the +X groove clearance to 1.105; the real value is 1.020 (table (a)).

No part or placement was changed. Raw numbers: `reference/fit-check.json`.
