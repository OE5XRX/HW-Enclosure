# Logo source

- `oe5xrx-full.svg`: verbatim copy of `logo/oe5xrx-full.svg` from
  [OE5XRX/branding](https://github.com/OE5XRX/branding), commit
  `eec51928d8f8d6b362d2a84cd83fc8cb3c1957dd` (main, 2026-08-30).
  Fetched with
  `gh api "repos/OE5XRX/branding/contents/logo/oe5xrx-full.svg?ref=eec51928d8f8" -q .content | base64 -d`.
- `oe5xrx-full-outlined.svg`: generated, do not edit:
  `python3 tools/outline_svg.py desktop/logo/oe5xrx-full.svg desktop/logo/oe5xrx-full-outlined.svg --width 80`.
  The mark's strokes (width 5 in a `scale(0.75)` group, round caps/joins) are
  replaced by their outlines and everything is united into 19 simple loops
  (12 outer boundaries, 7 holes), curves flattened with a chord error of
  0.01 user units (0.005 mm). Its viewBox is the logo's own bounding box:
  160.007 x 138.590 user units.
  SolidCraft's `sketch.insert_svg` imports only the centrelines of stroked
  paths (no width, no profiles), which is why the outlining is needed.

## Placement on the cover plate (`desktop/parts/deckplatte.sc`)

- Width 80 mm (longer side), height 69.29 mm; scale 0.499978 mm per SVG user
  unit (80 / 160.007), centred on the plate centre (0, 0), on top face z = T.
- Raised `logo_h` = 0.6 mm. Outlined area 855.83 mm^2, so the logo adds
  855.83 x 0.6 = 513.50 mm^3 (plate 38513.53 -> 39027.03 mm^3).
- Smallest features at this scale: mark strokes 1.875 mm (5 x 0.75 x 0.5),
  wordmark strokes >= ~1.87 mm, lightning bolt body down to ~0.97 mm; only the
  bolt's pointed tips taper below 0.8 mm (inherent to the branding shape).
