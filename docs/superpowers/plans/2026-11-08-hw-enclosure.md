# HW-Enclosure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the reconstructed desktop enclosure into the public repo `OE5XRX/HW-Enclosure` with all parts, the new branding logo, checked-in PCB STEPs and a station assembly that proves the modules fit.

**Architecture:** Parts are parametric SolidCraft designs (`.sc`) driven through SolidCraft's MCP server. A small Python checker talks to that server and asserts each part's volume, bounding box and timeline health, so every CAD step has a test. PCB STEPs come from `kicad-cli` via a guarded export script. `desktop/station.sc` links the parts and imports the STEPs. Positions come from a written derivation (hole patterns + KiCad data), not by eye.

**Tech Stack:** SolidCraft 0.27.1 (`solidcraft --control 7878`, MCP via `solidcraft-cli mcp --connect 127.0.0.1:7878`), KiCad 10.0.5 `kicad-cli`, Python 3 (stdlib only), Bash, `gh`.

**Spec:** `docs/superpowers/specs/2026-11-08-hw-enclosure-design.md`

## Global Constraints

- Repo: `OE5XRX/HW-Enclosure`, public, license CERN-OHL-S-2.0 (copy `LICENSE` from `../HW-Module-BusBoard`).
- Everything enclosure-specific under `desktop/`; `rack-19/` is only a README placeholder.
- Never commit STL, 3MF or G-code. Do commit `.sc`, `.step`, PCB STEPs.
- PCB STEPs only from each module repo's `origin/main`; record repo + commit in `pcb/SOURCES.md`.
- DeviceTester exported twice: full and `--variant Slot --no-dnp`.
- Per station: 1 × grundgestell (normal), 1 × grundgestell-gespiegelt, 2 × deckplatte (front, back), 4 × leiste (2 per frame).
- Slots: 1 PowerBoard, 2 CM4Carrier (both fixed by the BusBoard), 3–6 FMTransceiver. DeviceTester not placed.
- New logo = `OE5XRX/branding` `logo/oe5xrx-full.svg`, outlines as in the branding (no editable text), 0.6 mm raised.
- Reconstructed part dimensions must not change. Any fit problem is reported to the user, not fixed silently in the enclosure.
- Every saved `.sc` must reopen with no feature `error` and no `rolled_back` feature (a saved rolled-back marker silently dropped the old logo once).
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; PR bodies end with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## Review Focus

1. **Saved design with a rolled-back marker** → reopens without the last features. `tools/check_parts.py` fails on any `rolled_back` feature (Task 1).
2. **Module repo not on `origin/main`** (FMTransceiver is locally on `kicad_branch_update`) → the export must refuse, not export the branch (Task 2 test).
3. **Mirrored vs. normal frame swapped** → the groove check gives a false pass/fail. The normal frame's COM x must be the negative of the mirrored one's (Task 3 test).
4. **SVG strokes** (`stroke-width` lines in the branding mark) import as zero-area curves → logo partly missing. The logo test checks the added volume against the outlined SVG's area (Task 4).
5. **Hole patterns that don't line up** (BusBoard holes vs. the 20 mm pocket pitch, deckplatte's asymmetric holes) → stop and report instead of nudging parts (Task 5 decision gate).

---

## File Structure

```
HW-Enclosure/
├── LICENSE, README.md, .gitignore
├── tools/
│   ├── sc_mcp.py          MCP stdio client for the running SolidCraft app
│   └── check_parts.py     asserts expected numbers for every part/assembly
├── desktop/
│   ├── parts/             leiste.sc/.step, deckplatte.sc/.step,
│   │                      grundgestell.sc/.step (normal), grundgestell-gespiegelt.sc/.step
│   ├── logo/              oe5xrx-full.svg (+ SOURCE.md), oe5xrx-full-outlined.svg
│   └── station.sc         assembly
├── pcb/
│   ├── export-steps.sh    guarded kicad-cli export
│   ├── SOURCES.md         generated: module, repo, commit, file
│   └── *.step
├── reference/
│   ├── reconstruction.md  G-code → dimensions method and uncertainties
│   ├── assembly.md        derived placements (Task 5)
│   └── fit-check.md       interference results (Task 7)
├── rack-19/README.md
└── docs/superpowers/{specs,plans}/
```

Starting material: `~/oe5xrx/station-case/` (`cad/`, `gcode/`, `docs/`). The repo is created by turning this folder into the repo; `gcode/` stays on disk, ignored.

---

### Task 1: Repo scaffold, part checker, existing parts

**Files:**
- Create: `.gitignore`, `LICENSE`, `README.md` (stub: title, one paragraph, "WIP"), `rack-19/README.md`, `tools/sc_mcp.py`, `tools/check_parts.py`
- Move: `cad/leiste.{sc,step}` → `desktop/parts/`, `cad/deckplatte.{sc,step}` → `desktop/parts/`, `cad/grundgestell.{sc,step}` → `desktop/parts/grundgestell-gespiegelt.{sc,step}`; `cad/logo_2025.dxf` → `reference/logo_2025.dxf`; delete `cad/*.stl`

**Interfaces:**
- Produces: `tools/sc_mcp.py`: `class SolidCraft: __init__(port=7878, allow_paths: list[str]=[])`, `call(tool: str, args: dict) -> dict` (parsed JSON; raises `SolidCraftError` on tool or JSON-RPC error), `execute(command: str, params: dict) -> dict`, `batch(commands: list[dict]) -> dict`, `open(path)`, `measure() -> dict`, `timeline() -> list[dict]`.
- Produces: `tools/check_parts.py`: `EXPECTED: dict[str, Expect]` with `Expect(volume: float, bbox_min: tuple, bbox_max: tuple, com_x: float|None, tol_vol=0.5)`; CLI `python3 tools/check_parts.py [name ...]` exits 0 only if every named part (default: all) opens, has no feature error, no `rolled_back` feature, and matches.

- [ ] **Step 1: `.gitignore`** with `*.stl`, `*.3mf`, `*.gcode`, `.~*.lock`, `gcode/`, `__pycache__/`, `*.kicad_prl`.
- [ ] **Step 2: Write `tools/check_parts.py` with these entries first** (values measured 2026-11-08):

```python
EXPECTED = {
  "desktop/parts/leiste.sc":     Expect(3419.76,  (-68, -4.25, 0), (68, 4.25, 3)),
  "desktop/parts/deckplatte.sc": Expect(39783.31, (-58.5, -55, 0), (58.5, 55, 3.6)),
  "desktop/parts/grundgestell-gespiegelt.sc":
                                 Expect(97892.06, (-68, -60, 0), (68, 60, 20), com_x=1.957),
}
```
- [ ] **Step 3: Run it before moving files** → `python3 tools/check_parts.py` FAILS (files not found).
- [ ] **Step 4: Implement `sc_mcp.py`** (JSON-RPC 2.0 over stdio to `solidcraft-cli mcp --connect 127.0.0.1:7878 --allow-path <repo>`; `initialize` then `notifications/initialized`; treat both `error` and `result.isError` as failure). Move the files as listed.
- [ ] **Step 5: Run** `python3 tools/check_parts.py` → all 3 PASS. Also temporarily roll `deckplatte.sc` back one feature (`timeline.roll_to {position: 3}`), save to a scratch copy, run the checker on it → FAIL "rolled_back: Logo". Discard the copy.
- [ ] **Step 6: Create repo + first push**

```bash
git init -b main && git add -A && git commit -m "chore: scaffold HW-Enclosure with reconstructed desktop parts"
gh repo create OE5XRX/HW-Enclosure --public --source . --push \
  --description "3D-printed enclosures for the OE5XRX remote station (desktop, 19-inch planned)"
```

### Task 2: PCB STEP export

**Files:**
- Create: `pcb/export-steps.sh`, `pcb/test-export-guard.sh`; Generate: `pcb/SOURCES.md`, `pcb/*.step`

**Interfaces:**
- Produces: `pcb/export-steps.sh [MODULES_DIR]` (default `..`), writes `pcb/BusBoard.step`, `pcb/PowerBoard.step`, `pcb/CM4Carrier.step`, `pcb/FMTransceiver.step`, `pcb/DeviceTester.step`, `pcb/DeviceTester-slot.step`, and `pcb/SOURCES.md` (table: module | repo | commit | file | kicad-cli version).
- Guard: for each `HW-Module-<X>`: `git fetch`; refuse (exit 2, message names the repo) if the working tree has changes to tracked files or `HEAD != origin/main`. It never switches branches itself. Project file = the single `*.kicad_pcb` at repo root.
- Export: `kicad-cli pcb export step --subst-models --force -o <file> <pcb>`; slot: add `--variant Slot --no-dnp`.

- [ ] **Step 1: Write `pcb/test-export-guard.sh`**: copies one module repo to a temp dir, (a) checks out a new branch with one extra commit → expects exit 2 and the repo name on stderr; (b) modifies the `.kicad_pcb` → exit 2; (c) clean `origin/main` → exit 0 and a non-empty STEP.
- [ ] **Step 2: Run it** → FAIL (script missing).
- [ ] **Step 3: Implement `export-steps.sh`**.
- [ ] **Step 4: Run the guard test** → PASS.
- [ ] **Step 5: Real export.** FMTransceiver is locally on `kicad_branch_update`: the script must refuse it. Do **not** switch the user's branch; instead clone fresh into a temp dir (`gh repo clone OE5XRX/HW-Module-<X> /tmp/...`) and run `export-steps.sh <tempdir>`. Verify: 6 STEPs, sizes roughly BusBoard 1.2 MB, PowerBoard 1.1, CM4Carrier 15, FMTransceiver 5.4, DeviceTester 3.3, DeviceTester-slot 2.5; `grep -c "'J203'" pcb/DeviceTester-slot.step` = 0, same in `DeviceTester.step` = 1.
- [ ] **Step 6: Commit** `pcb/` → "feat(pcb): export module STEPs from origin/main".

### Task 3: Normal (non-mirrored) frame

**Files:**
- Create: `desktop/parts/grundgestell.sc`, `desktop/parts/grundgestell.step`; Modify: `tools/check_parts.py`

**Interfaces:**
- Consumes: `grundgestell-gespiegelt.sc` (Task 1).
- Produces: `grundgestell.sc`, body named `Grundgestell`, same parameters as the mirrored one.

- [ ] **Step 1: Add the expectation** `"desktop/parts/grundgestell.sc": Expect(97892.06, (-68,-60,0), (68,60,20), com_x=-1.957)`. Run → FAIL (missing).
- [ ] **Step 2: Build.** Open `grundgestell-gespiegelt.sc`, append `solid.mirror {bodies: [<body>], plane: "YZ"}`, remove the original body from the result (e.g. `body.delete` / keep only the mirror, whatever SolidCraft offers — the parameters must still drive the result), rename body to `Grundgestell`, `save` as `grundgestell.sc`, `export` `.step`. Rename the mirrored file's body to `Grundgestell-gespiegelt` and re-save it.
- [ ] **Step 3: Run** `check_parts.py` → PASS for both frames (COM x flips sign, volume equal).
- [ ] **Step 4: Parameter test:** `set_parameter margin=9 mm` in `grundgestell.sc` → volume unchanged, COM x moves; undo without saving.
- [ ] **Step 5: Commit** "feat(desktop): add normal frame as mirror of reconstructed frame".

### Task 4: Cover plate with the branding logo

**Files:**
- Create: `desktop/logo/oe5xrx-full.svg` (copy), `desktop/logo/SOURCE.md` (branding repo commit SHA), `desktop/logo/oe5xrx-full-outlined.svg`, `tools/outline_svg.py`; Modify: `desktop/parts/deckplatte.sc/.step`, `tools/check_parts.py`

**Interfaces:**
- Produces: `tools/outline_svg.py in.svg out.svg` → an SVG whose every visible shape is a filled path (strokes converted to their outline, honouring `stroke-width`, round caps/joins as in the source, group `transform`s applied), plus printing the total filled area in mm² for the target width.

- [ ] **Step 1: Copy** `logo/oe5xrx-full.svg` from `OE5XRX/branding` (`gh api repos/OE5XRX/branding/contents/logo/oe5xrx-full.svg`), note the commit SHA in `SOURCE.md`.
- [ ] **Step 2: Outline the strokes.** No inkscape/svg library is installed; `outline_svg.py` (stdlib) may handle exactly what this file uses: `path` with `M L a A Z` and `Q`, `circle`, `g transform="translate() scale()"`, `stroke-linecap/linejoin="round"`. An arc/line stroke of width w becomes its offset outline with round caps. Verify by rendering both SVGs (`kicad-cli` is not an SVG renderer; use SolidCraft `sketch.insert_svg` + screenshot) and comparing visually; the outlined one must have no hairlines.
- [ ] **Step 3: Pick size and place.** Logo fits the old logo frame area: ≤ 80 mm on its longer side, centred at the plate centre (the old logo's +1.55/−0.07 offset was a print artefact of the 2025 logo, not a requirement). Record the scale in `SOURCE.md`. Compute the expected added volume = outlined area at that scale × 0.6 and put the total into `check_parts.py` (`Expect(38513.53 + area*0.6, (-58.5,-55,0), (58.5,55,3.6))`). Run → FAIL (old logo still there).
- [ ] **Step 4: Replace in `deckplatte.sc`:** delete features `Logo` and `LogoSketch`, add sketch `LogoSketch` on `{"plane":"XY","offset":"T"}` with `sketch.insert_svg {path: outlined svg, width: <mm>, align: "center", at: [0,0]}`, extrude `logo_h` join, name `Logo`. Ensure the marker is at the end, save, export `.step`.
- [ ] **Step 5: Run** `check_parts.py deckplatte` → PASS; top-view screenshot attached to the commit's PR/notes and visually matches the branding.
- [ ] **Step 6: Commit** "feat(desktop): cover plate with current OE5XRX branding logo".

### Task 5: Derive the assembly placement (decision gate)

**Files:**
- Create: `reference/assembly.md`

**Interfaces:**
- Produces: a table of every occurrence in `station.sc`: name, source file, translation `[x,y,z]` mm, rotation (axis + angle), and the measured evidence for it. Coordinate system: origin at the centre of the bottom frame's underside, +Y towards the front (open groove side), +Z up.

- [ ] **Step 1: Collect hole/edge data** from the KiCad boards with `kicad-cli pcb export pos` / reading the `.kicad_pcb` (board outline `Edge.Cuts`, `MountingHole*` footprints, connector refs and their pads): BusBoard mounting holes and the 6 slot connectors (pitch, which end is slot 1 = PowerBoard), each module's board outline (expected 100 × 100) and bus connector position.
- [ ] **Step 2: Match to the parts:** frame back pockets (6 × Ø5 at x = −50 + 20·i, z = 10, back face y = −54), groove centres (x = −44 + 20·i), side/front bores, leiste holes (Ø3.2, 100 mm apart), deckplatte holes (from its corner: (8|4.5), (9|105.5), (112|10), (112|100)). Write down which hole meets which and the resulting transforms; normal frame bottom, mirrored frame on top (grooves facing down) unless the evidence says otherwise.
- [ ] **Step 3: Gate.** If any pattern doesn't match within 0.3 mm, or a part's position is ambiguous, STOP and report the finding to the user with the numbers. Otherwise commit "docs(reference): derive station assembly placement".

### Task 6: Station assembly

**Files:**
- Create: `desktop/station.sc`; Modify: `tools/check_parts.py`

**Interfaces:**
- Consumes: parts (Tasks 1, 3, 4), STEPs (Task 2), placements (Task 5).
- Produces: `station.sc` with linked components (`component.insert_design`, paths relative to the repo) and STEP components (`file.insert_step`), named `Gestell`, `Gestell-gespiegelt`, `Deckplatte-vorne`, `Deckplatte-hinten`, `Leiste-1..4`, `BusBoard`, `Slot1-PowerBoard`, `Slot2-CM4Carrier`, `Slot3..6-FMTransceiver`.

- [ ] **Step 1: Checker entry** for `desktop/station.sc`: occurrence count = 16, each occurrence's bbox centre within 0.1 mm of the value implied by `assembly.md`, no feature errors. Run → FAIL.
- [ ] **Step 2: Build** with `component.insert_design` / `file.insert_step` and the transforms from Task 5 (ground the normal frame; fixed placements are fine — joints optional). Save.
- [ ] **Step 3: Run** checker → PASS. Re-open from a fresh clone path to prove relative links resolve (`component.links` → all `found`).
- [ ] **Step 4: Commit** "feat(desktop): station assembly with modules".

### Task 7: Fit check

**Files:**
- Create: `reference/fit-check.md`, `tools/fit_check.py`

**Interfaces:**
- Produces: `tools/fit_check.py` → for every pair (PCB occurrence, enclosure occurrence) and (PCB, PCB) reports intersection volume (SolidCraft interference/`inspect` command, or `solid.combine` intersect on copies in a scratch design) and the three spec questions: board edge in groove (clearance per side), connector mating (offset of module bus connector vs. BusBoard slot connector), BusBoard holes vs. pockets.

- [ ] **Step 1: Run it** and write `fit-check.md` with a pass/fail table and screenshots (iso + section through slot 2).
- [ ] **Step 2:** Any collision or misalignment → listed under "Findings" with numbers; tell the user. Do not change part dimensions.
- [ ] **Step 3: Commit** "docs(reference): station fit check".

### Task 8: Documentation and publish

**Files:**
- Modify: `README.md`; Create: `reference/reconstruction.md`

- [ ] **Step 1: `reconstruction.md`:** method (outer wall line width 0.4, `xy_hole_compensation` 0.27, layer grid 0.15 + n·0.2, layer-mid rule for heights), per-part measured vs. chosen values, and what is interpretation (Ø5 pockets as M3 heat-set inserts).
- [ ] **Step 2: `README.md`:** parts list with counts per station, print settings (PETG, 0.2 mm, 3 walls, 15 % infill — from the original G-code), hardware (M3 heat-set inserts, M3 screws), how to regenerate PCB STEPs (`pcb/export-steps.sh`), how to open `station.sc`, how to run `tools/check_parts.py`, a render of the assembly.
- [ ] **Step 3: Verify** `python3 tools/check_parts.py` passes for all; `git status` clean; `git ls-files | grep -E '\.(stl|3mf|gcode)$'` empty.
- [ ] **Step 4: Commit and push** "docs: README and reconstruction notes".
