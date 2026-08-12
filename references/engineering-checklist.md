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

Use measured hardware dimensions when available. Keep nominal dimensions and allowance separate. Treat generic FDM clearance numbers only as starting points; test-fit coupons are mandatory for expensive or long prints.

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
