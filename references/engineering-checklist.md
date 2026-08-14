# Engineering checklist

## 1. Requirements contract

Record these before modelling:

| Category | Questions |
| --- | --- |
| Object fit | What nominal width, thickness, diameter, depth, and insertion direction must fit? |
| Clearance | Is the fit sliding, loose, captured, magnetic, or press-fit? |
| Manufacturing | Printer volume, material, nozzle, layer height, minimum wall, support policy? |
| Assembly | Which blocks must remain separately movable or replaceable? |
| Access | From which sides must objects and cables enter or leave? |
| Orientation | Which face sits on the bed, base, wall, or table? |
| Edge treatment | Which edges qualify for a chamfer/fillet proposal (see criteria below), and which is the right kind for each? |
| Repetition | Does one shape appear more than once (a mirrored pair, or N placed copies like rover wheels, table legs, screw bosses)? If yes, how many, and at what position/rotation/mirror does each copy sit? |

Not every edge is a candidate. Use this to decide where to propose a treatment and where to say nothing:

Propose a treatment for:
- grip/handling edges (touched or held) → fillet, for comfort, unless a support/overhang concern outweighs it;
- insertion/lead-in edges (hole rims, slot mouths, connector openings) → chamfer, to guide the mating part in — fillets guide insertion less reliably;
- exposed outer corners on handled or bumped parts → light chamfer or fillet for safety/durability;
- load-bearing internal corners (rib-to-wall, wedge-to-base) → fillet, to reduce stress concentration and print-layer crack risk;
- steep overhang-start edges meant to print support-free → chamfer at a print-friendly angle, not a fillet.

Propose nothing (skip silently) for:
- fully internal/hidden edges never seen or touched (interior mating faces, concealed interior walls);
- edges carrying a validated critical-fit dimension, where any added radius/chamfer would change a clearance already fixed by this requirements contract, unless the treatment was already accounted for in that clearance;
- the bed-contact edge or a support-wedge contact edge, where a treatment would break flat bed contact or interrupt support continuity;
- edges below the printer's practical minimum feature size, where any proposed radius/chamfer would be unprintable.

For each edge where a treatment is proposed: a chamfer prints faster and rarely needs support, but feels sharper to the touch; a fillet is more comfortable and spreads stress better, but is sensitive to the printer's minimum feature radius and can need support on steep edges. Record the chosen kind and size as a named parameter per edge group (e.g. `edge_chamfer` or `edge_fillet_r`), the same way plan and profile radii are named.

When one shape is placed more than once — a mirrored pair, or an N-way pattern like 4 rover wheels — model it once and generate every copy from an `instances` list in `parameters.json` (name, position, rotation axis/angle, optional mirror normal), applied through the `add_instances` helper in [assets/freecad-parametric-template.FCMacro](../assets/freecad-parametric-template.FCMacro). Never hand-duplicate or hand-rotate geometry per copy — a wrong rotation typed twice is a common source of the "correct angle, wrong sign" trap. Deliver every instance as its own separate named STEP/STL component, consistent with not fusing logical assembly components into one anonymous body.

Use measured hardware dimensions when available. Keep nominal dimensions and allowance separate. Treat generic FDM clearance numbers only as starting points; test-fit coupons are mandatory for expensive or long prints.

### Heat-set insert hole sizing (starting point, not a fixed spec)

When a part takes a machine screw via a heat-set insert, size the pilot hole and boss from these typical ranges, then verify against the specific insert's datasheet — inserts of the same thread size vary in outer diameter and knurl geometry across brands:

| Thread | Typical pilot hole | Typical insert OD |
| --- | --- | --- |
| M2 | 3.0–3.2 mm | 3.2–3.5 mm |
| M3 | 4.0 mm | 4.0–4.6 mm |
| M4 | 5.6 mm | 5.6–6.3 mm |
| M5 | 6.4 mm | 6.4–7.1 mm |

Boss outer diameter: pilot hole + 2× minimum wall thickness (1.2–1.6 mm is a common starting wall for the boss, same `min_wall` parameter used elsewhere). FDM holes commonly print slightly undersized (nozzle over-extrudes on tight curves); a test-fit coupon is the reliable way to confirm the pilot hole before committing to the full print, consistent with the test-coupon rule above.

### Machine screw clearance holes and heads (reference the standard, don't retable it)

Plain machine screw geometry (clearance hole diameter, head diameter, counterbore/countersink depth) is tightly standardized — ISO 4762 (socket-head cap screws), ISO 7380 (button-head), and ISO 273 (clearance holes) — and varies far less across manufacturers than heat-set inserts do. Look these up from the relevant standard or the specific screw's datasheet at build time rather than keeping a second copy here that will drift out of date. If a supplied reference image shows the screw (SKILL.md's reference-image inspection step), read the head shape from it — hex socket, button, or flat/countersunk — and pick the matching standard instead of asking the user to name it; still confirm thread size and length, which usually aren't readable from a photo. Record whichever numbers were actually used as named parameters in `parameters.json` (e.g. `screw_clearance_d`, `screw_head_d`, `counterbore_depth`), same as every other dimension in this checklist.

## 2. Preliminary three-view drawing

Generate SVG and DXF from one parameterized 2D definition before creating BREP solids or meshes.

- Use aligned front, top, and right-side orthographic projections at one declared scale.
- Define which physical direction each view represents. Do not silently swap depth and width.
- Show the common overall X, Y, and Z envelope in the relevant pairs of views.
- Show every functional block as a separate labelled outline.
- Show object-fit envelopes and clearances, not only the plastic around them.
- Show insertion directions, open sides, cable entry and exit, MagSafe or other hardware pockets, retaining lips, angles, radii, and the print-bed plane.
- Add a section or hidden lines for internal channels, recess depths, wedges, and supports.
- Dimension from the same named parameters intended for CAD. Every critical dimension must have one authoritative value.
- Check cross-view consistency: a feature's X interval must match in front/top, Y in top/side, and Z in front/side.
- Resolve overlaps, floating blocks, inaccessible openings, and unsupported ledges in the drawing before modelling.
- Obtain user approval before 3D generation. Skip the pause only when the user explicitly requests an uninterrupted run; in that case, record every assumption visibly.
- Render and inspect the SVG as the human review surface.
- Keep DXF model-space geometry at 1:1 in millimetres; never derive its units from SVG pixels.
- Use separate DXF layers for visible outlines, hidden lines, centre lines, dimensions, and text.
- Prefer editable `LINE`, polyline, arc, text, and dimension entities over one flattened outline when interoperability allows it.

The approved drawing is the geometry contract. Any material design change requires a revised preliminary drawing and revision mark. After modelling, create fresh projections from the actual 3D geometry and compare them with this contract.

## 3. Coordinate and transform discipline

Use a documented right-handed system, normally:

- X: left/right;
- Y: front/back;
- Z: up;
- base bottom: Z = 0;
- top of base: Z = `base_h`.

For rotation by angle `a` around X:

```text
y' = y*cos(a) - z*sin(a)
z' = y*sin(a) + z*cos(a)
```

Apply translation after rotation. Compute transformed extrema from every relevant local boundary, including thickness, shelf depth, and fillet extents.

For a plate with local thickness `t` along +Y rotated backward by `a < 0`, place its back lower edge on a base plane `Zb` with:

```text
placement_z = Zb - t*sin(a)
```

For a local support edge that must become horizontal after rotation:

```text
dz/dy = -tan(a)
```

Derive the wedge from the whole supported Y interval, not from the plate alone.

## 4. Support-free geometry

Check the actual print orientation.

- No functional block may float above the base.
- A shelf support must cover the shelf's full X interval. Compare exact `min_x` and `max_x`; a symmetric-looking inset can still leave one side unsupported.
- Fill the underside from the deepest front projection through the rear contact edge.
- Prefer a continuous wedge for a no-support requirement. Use ribs only when their spacing and bridge length are acceptable and explicitly validated.
- Keep wedge bottoms horizontal after Placement rotation.
- Avoid trapped support inside narrow cable channels, magnetic pockets, or blind recesses.
- Shallow open recesses may bridge, but never assume a large circular horizontal pocket is support-free without checking depth and orientation.
- A rounded outline does not imply rounded printable edges. Treat plan radii, profile radii, and fillets independently.

## 5. Channels and pockets

Build outer solids first, fuse them, then subtract continuous tools.

For a cable route, verify all segments:

1. device pocket;
2. vertical or radial channel;
3. shelf/ledge crossing;
4. support wedge crossing;
5. base slot;
6. accessible exit.

Make the base slot wide enough for the cable or connector strategy. Prefer an open-edge slot when the connector cannot be threaded through a closed hole. Round cable-contact edges where practical.

## 6. Open access

Interpret “open from either side” literally:

- omit side solids;
- avoid a cosmetic outline or hidden compound that closes the opening;
- validate an empty region between retaining walls;
- preserve the front/back spacing while allowing lateral translation.

Disconnected walls may remain one logical component in STEP/FreeCAD so they move together through Placement.

## 7. Deliverable checks

### Preliminary drawing

- front, top, and right-side projections are present and aligned;
- shared extents and feature positions agree between views;
- critical fit, clearance, angle, radius, wall, recess, and cable dimensions are shown;
- separately movable blocks and Placement intent are identifiable;
- unresolved assumptions are called out;
- approval or an explicit assumption record exists before 3D generation.

### SVG

- valid XML and a declared `viewBox`;
- vector geometry rather than an embedded raster screenshot;
- visible dimensions, labels, revision, units, and projection convention;
- rendered and visually inspected for overlap, clipping, and unreadable text.

### DXF

- valid ASCII or binary DXF structure with an `EOF` terminator;
- millimetre units and model-space geometry at 1:1;
- visible, hidden, centre, dimension, and text layers are present when used;
- front, top, and right-side geometry matches the SVG dimensions;
- editable line, arc, polyline, text, and dimension entities are preferred over a traced bitmap outline;
- projection labels, revision, and critical dimensions are present.

### STL

- structurally valid binary or ASCII STL;
- finite coordinates;
- expected bounds;
- no vertices below the bed;
- required contact span at the bed/base plane;
- requested empty regions contain no triangle centroids;
- no unintended disconnected floating shells (`validate_stl.py --expect-components`);
- manifold/watertight topology: every edge shared by exactly two triangles, with consistent winding (no flipped normals).

### STEP

- starts with `ISO-10303-21;`;
- ends with `END-ISO-10303-21;`;
- contains `MANIFOLD_SOLID_BREP` or equivalent BREP representation;
- contains expected named products/components;
- names and revision match delivered files.

### Drawing

- top, front, side, and critical section when needed;
- nominal sizes, clear sizes, radii, angles, and derived clearances;
- Placement table for multi-block assemblies;
- print orientation and support policy;
- revision mark;
- final SVG and DXF views are generated from the completed 3D model and match the approved preliminary drawing;
- rendered and visually inspected for overlap or clipping.

## 8. Iteration traps

- Correct angle, wrong sign.
- Correct sign, but rotated thickness collides with the next block.
- Stand moved for clearance, then left floating above the base.
- Center wedge added, but shelf remains cantilevered at one or both X edges.
- Cable cut reaches the pocket but stops at the shelf or wedge.
- Side walls removed in the drawing but retained in STL.
- STEP exported as one anonymous part despite a movable-block requirement.
- Old revision linked after geometry changed.
- Perspective concept image mistaken for an orthographic engineering view.
- 3D modelling started before contradictory dimensions across views were resolved.
- Preliminary drawing updated after a change, but final model-derived projections were not compared against it.
- SVG looks correct, but DXF was exported in pixels or at an arbitrary scale.
- SVG and DXF were authored separately and disagree on a critical dimension.
- DXF contains one flattened traced outline instead of useful editable CAD entities.
