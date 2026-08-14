# Print-in-place joints

Read this only when [engineering-checklist.md](engineering-checklist.md) §1's "Print-in-place mechanism" row applies — not on every task.

A print-in-place joint (hinge, swivel) prints already assembled: two parts with a functional gap between them, no post-print assembly, no access to remove support from inside the gap afterwards. Currently implemented: `pin_in_sleeve` (a pin rotating inside a sleeve), via `build_print_in_place_joint` in [assets/freecad-parametric-template.FCMacro](../assets/freecad-parametric-template.FCMacro), sized by [scripts/print_in_place.py](../scripts/print_in_place.py). Extend the same way for a ball-and-socket or a living hinge when one is actually needed.

Schema (`parameters.json`):

```json
"print_in_place_joint": {
  "type": "pin_in_sleeve",
  "pin_radius": 2.0,
  "pin_height": 10.0,
  "radial_clearance": 0.25,
  "axial_play": 0.3,
  "wall_thickness": 1.2,
  "standoff_from_bed": 1.0,
  "lead_in_chamfer": 0.6,
  "bore_relief": {"count": 3, "width_deg": 20, "depth": 0.3}
}
```

`lead_in_chamfer` and `bore_relief` are both optional — omit either for a plain cylindrical pin/sleeve.

What's easy to miss:

- **Joint axis must be vertical.** A pin-in-sleeve gap prints cleanly only when its axis is perpendicular to the bed — every layer is then just two concentric circles with a gap, no bridging. A horizontal axis turns the gap into a bridge the nozzle crosses mid-layer, risking sag that welds the pin to the sleeve. This is not just a joint setting: it constrains which face of the whole part can sit on the bed (§1 "Orientation"), so resolve them together, not independently.
- **Radial clearance and axial play are not the same number.** Radial clearance keeps the pin from binding as it turns; axial play keeps the pin's ends from fusing to the sleeve's ends. They fail for different reasons (friction vs. elephant's foot) and should stay separate parameters.
- **Standoff from the bed, don't let the joint sit on it.** The first few layers bulge slightly (elephant's foot); if the joint's gap is at Z=0 that bulge is exactly where it closes the gap. `standoff_from_bed` lifts the whole joint clear of that zone.
- **The open end of the joint must pass the overhang check.** There's no way to clear support out of a sealed gap after printing, so run [scripts/validate_stl.py](../scripts/validate_stl.py)'s `--max-overhang` check specifically against the joint's exposed faces, not just the part as a whole.
- **Print a coupon of the joint itself, not a generic hole.** `build_coupon_plate` (test-coupons) cuts holes/slots in a flat plate — it doesn't replicate the local wall thickness, mass, and cooling behaviour around an actual pin-in-sleeve. Use `build_print_in_place_coupon` (below) to print a small standalone version of the real joint first, rather than a hole/slot standing in for it.
- **PETG and similar sticky materials need looser clearances than PLA.** Don't reuse a PLA-tuned `radial_clearance`/`axial_play` on a different material without saying so.
- **Printed-plastic-on-plastic wears faster than metal.** If the mechanism needs many duty cycles, say so to the user up front — this is a durability limit of the technique, not a bug in the geometry.
- **`bore_relief` trades full-surface contact for a few small lands, same principle as the herringbone-vs-ball-bearing correction below.** A plain full-circle bore contacts the pin along its entire circumference — more surface to fuse or bind. `bore_relief` cuts the bore oversized everywhere except at `count` narrow lands (flat-box approximation of the true arc, good for `width_deg` ≤ ~30°) that are the only surfaces actually touching the pin. This lets you run a *tighter* `radial_clearance` at those lands than a full-circle bore could tolerate, at the cost of a small amount of play between lands (the joint isn't perfectly round-riding anymore) and one more thing to get printed cleanly. Start with 3 lands; more lands trend back toward full-surface contact, fewer than 3 under-constrain the pin radially.
- **`lead_in_chamfer` eats into the pin's effective length.** It chamfers the pin's top/bottom circular edges so a slightly fused joint is easier to twist free without cracking the sleeve wall — cheap and close to risk-free, but remember the chamfered length is inside the `axial_play` gap, not extra length on top of it; don't stack a generous chamfer on top of a tight `axial_play` without checking the two still add up sensibly.

## Testing radial and axial together

`radial_clearance` and `axial_play` interact — a combination that looks fine tested one dimension at a time (like the plate-based `test_coupons` mechanism) can still fuse or bind once both are near their tight end together. `build_print_in_place_coupon` in [assets/freecad-parametric-template.FCMacro](../assets/freecad-parametric-template.FCMacro) lays out one small pin+sleeve pair per combination on a grid, from `parameters.json`'s `print_in_place_joint_coupon`:

```json
"print_in_place_joint_coupon": {
  "pin_radius": 2.0,
  "pin_height": 6.0,
  "wall_thickness": 1.2,
  "radial_values": [0.15, 0.2, 0.25],
  "axial_values": [0.2, 0.3, 0.4],
  "margin": 8.0,
  "standoff_from_bed": 1.0
}
```

Rows vary `radial_clearance`, columns vary `axial_play`, in the order given — record which grid cell was picked the same way a `test_coupons` trial value gets recorded, then fix both chosen numbers in the real `print_in_place_joint`. `spacing` auto-sizes from the largest sleeve OD in the grid when omitted, so cells never overlap.

## Adding a joint type this file doesn't cover yet

Only `pin_in_sleeve` ships in the shared template. When a task needs a different joint (ball-and-socket, living hinge, a multi-knuckle hinge, a print-in-place chain, ...), build it in that task's own project copy of the macro — don't wait for the shared skill to grow a matching type first. Follow `pin_in_sleeve` as the template:

1. **Pure geometry math, no FreeCAD.** A small module like [scripts/print_in_place.py](../scripts/print_in_place.py) — plain functions computing radii/dimensions from clearance and play, with an `if __name__ == "__main__":` assert-based self-check. Keep it FreeCAD-free so it's testable with plain `python3`.
2. **A `build_<type>_joint(doc, assembly, params_doc)` function in the project's FCMacro**, modelled on `build_print_in_place_joint`: read its config from a new or extended `print_in_place_joint` entry, build each half as a *separate* solid via `add_block` (never fuse — same rule as every other assembly), keep radial/lateral clearance and axial/end-float play as distinct parameters, and add a `standoff_from_bed` if any face of the joint could sit in the elephant's-foot zone.
3. **Multi-copy joints (knuckle hinge, chain, snake-arm) don't need new geometry at all** — model one knuckle/link and place every copy through the existing `add_instances` helper and an `instances` list, exactly as for rover wheels or screw bosses ([engineering-checklist.md](engineering-checklist.md) §1 "Repetition"). Only write a new `build_*_joint` function when the unit itself (not its repetition) is a new shape.
4. **Reuse `validate_stl.py --max-overhang`** on the joint's exposed/open faces — don't write a new overhang checker.
5. **Print a coupon of the new joint itself** before the full part, same reasoning as the "print a coupon of the joint itself" point above — a hole/slot coupon from `build_coupon_plate` doesn't stand in for it.
6. **Update `engineering-checklist.md`'s "Print-in-place mechanism" row and this file** only if the new type turns out to be broadly reusable across tasks, not on the first one-off use — that's the same bar `test_coupons` and `pin_in_sleeve` had to clear before joining the shared skill.

Known starting points, so a session doesn't have to invent the physics from scratch:

- **`ball_socket`** (a ball rotating inside a socket, for multi-axis joints): size the socket inner radius as `ball_radius + radial_clearance` (same clearance reasoning as `pin_in_sleeve`); the socket opening angle (how far the socket wraps around the ball) is what has to pass the overhang check — a socket that wraps past roughly 90° from the opening axis creates a downward-facing cavity ceiling that needs the same `--max-overhang` scrutiny as any other unsupported overhang, and there's no way to support it internally. Keep the ball's own support/retention (how it's captured before the socket is closed) as an explicit modelling step, not an afterthought.
- **`living_hinge`** (a thinned flexible membrane instead of a clearance gap): typical starting thickness is 0.3–0.6 mm for PLA, nearer 0.4–0.6 mm for PETG (PETG is more flex-fatigue-resistant but needs a touch more thickness to avoid tearing on the first bend) — always confirm with a coupon before committing, per the material-sensitivity point above. Orient the hinge line so the layers run *along* the fold, not across it: folding across layer lines is what cracks the hinge after a handful of cycles.
- **Multi-knuckle hinge / chain / snake-arm** — not a new type at all; see point 3 above. Model one `pin_in_sleeve` (or `ball_socket`) knuckle/link and repeat it via `instances`.
- **Chevron/helical self-retaining pin** (a pin that can't walk out axially without needing a precisely tuned `axial_play`): a genuinely more elegant fix for axial drift than tolerancing `axial_play` tighter, but a real recipe, not shipped code — a swept helical boolean is enough riskier to get right blind (no FreeCAD session here to verify the sweep) that it isn't worth building speculatively for a rarely-needed case. Construction: cut two opposed helical grooves into the pin (`Part.makeHelix(pitch, height/2, pin_radius)` swept with a small circular or V-shaped cutting profile, once with a positive lead and once mirrored/reversed), meeting exactly at the pin's mid-height so the two helix senses cancel — like herringbone gear teeth, this is what gives it zero net axial thrust instead of screwing itself out in one direction as it turns. The sleeve gets the matching internal helical land (or, more forgivingly, stays smooth and just rides the crest of the pin's helix — trading some retention for a much simpler sleeve). Confirm with a coupon before committing, same as every other joint here; expect a few iterations on pitch/depth, since this one is far more sensitive to actual clearance than a straight pin_in_sleeve.
- **Printed cantilever spring** (a flexing beam for a latch or clip, not a metal coil): model the shape parametrically (beam length, width, thickness), but do not report a computed stiffness or force as exact — FDM's layer-direction strength is anisotropic in a way simple beam formulas (`δ = FL³/(3EI)`) don't capture, so any number from that formula is a rough starting estimate, not a spec, same caveat `estimate_material.py` already carries for weight. State it as such, then confirm the actual deflection/force with a printed coupon — do not skip the coupon step because a formula "already" gave a number. Keep beam strain within the material's known-safe elastic range (a rule of thumb, not a value to invent per material) to avoid the beam taking a permanent set after a few cycles.
- **Ratchet/pawl**: a sawtooth profile (steep ~80–90° engagement face, shallow ~20–30° release face) plus a pawl arm that is itself a printed cantilever spring — so it inherits every caveat above, and depends on the pawl arm's spring being built first. Treat this as a composite of two already-covered pieces (tooth profile geometry + cantilever spring), not a new physics problem.
- **Printed ball/roller bearing** (captured spherical balls or cylindrical rollers riding in a groove between two rings): still a poor trade for FDM specifically because it's *point/line contact* — it needs the groove and the ball diameter toleranced tightly against each other, and a ball that isn't perfectly round (FDM rarely prints a good sphere) either binds or falls out. Flag this to the user before building one; a $1 608 bearing (see [standards-catalog.md](standards-catalog.md)) beats it outright on effort and durability. Build it only if the user explicitly wants an all-printed part with no bought hardware.
- **Herringbone planetary gear bearing** — a genuinely good print-in-place low-friction rotary bearing, and a different mechanism from the ball/roller case above: rotation happens through meshing gear teeth (a ring gear plus several planet gears, herringbone/chevron tooth profile) rather than point contact on a raceway. This works well on FDM precisely because gear teeth are far more tolerant of layer-resolution inaccuracy than a captured sphere is, and the herringbone (chevron, i.e. two opposed helix angles meeting at the tooth centre) profile self-centres axially and cancels out thrust load, which is what keeps it from binding or walking sideways as it spins. Starting points: 3 evenly-spaced planet gears is the common baseline; pick a module large enough that tooth roots and tips stay above the printer's minimum feature size (roughly module 1.5–2.5 mm on a typical 0.4 mm-nozzle desktop FDM printer); add backlash (extra flank clearance) rather than a raw radial clearance — 0.1–0.2 mm per flank is a reasonable PLA starting point, looser for PETG per the material-sensitivity point above; keep the axis vertical, same reasoning as `pin_in_sleeve` — each layer then prints a consistent full gear cross-section with no bridging across the tooth gaps. Confirm backlash and spin freedom with a coupon (a short axial slice of the ring + one or two planets) before committing to the full-height part.
- **Dovetail / T-slot slider**: not a print-in-place joint type — it's an ordinary sliding clearance fit, already covered by the `clearances` section and the "Clearance" row in engineering-checklist.md §1. No new schema or geometry pattern needed.
- **Snap-fit latch**: a different family from print-in-place (it's a post-print assembly aid, not a mechanism printed already-moving) — deferred separately; see `plan/` for the retention-feature backlog rather than building it here.
