---
name: design-parametric-3d-prints
description: Design and revise functional, parameterized parts for FDM 3D printing, including organizers, holders, mounts, adapters, spacers, enclosures, cable routes, and multi-block assemblies. Use when Codex must first turn dimensional requirements or reference images into an approved three-view SVG plus an editable 1:1 DXF, then create editable FreeCAD-compatible geometry, named STEP components, print-ready STL, and final model-derived drawings; especially when fit clearances, Placement/Move assembly, support-free printing, overhang removal, bed contact, or iterative CAD revision must be verified.
---

# Design Parametric 3D Prints

Create fabrication-ready parametric CAD, not merely a plausible render. Freeze the intended geometry in a dimensioned three-view drawing before building 3D. Keep every dimension traceable, every block movable, and every printability claim backed by geometry checks.

## Required workflow

1. Read [references/engineering-checklist.md](references/engineering-checklist.md) before generating geometry.
2. Inspect supplied reference images, CAD, or slicer screenshots. Treat observed collisions, floating parts, unintended walls, and overhangs as geometric evidence.
3. Convert the request into three parameter groups:
   - nominal object dimensions;
   - manufacturing clearances and radii;
   - derived dimensions and placements.
4. State the coordinate system and print orientation. Use millimetres unless the user specifies otherwise.
5. Generate the preliminary three-view drawing from the parameter table before creating any 3D solid:
   - SVG for immediate visual review;
   - DXF in millimetres and model space 1:1 for editable CAD geometry.
   Keep their front, top, and right-side projections identical. Show the overall envelope, block boundaries, openings, object clearances, angles, radii, cable routes, and print-bed plane.
6. Validate both files, then present the SVG for user approval and provide the DXF as the engineering source. Pause before 3D modelling unless the user explicitly requested an uninterrupted run without intermediate confirmation. Never proceed while a material contradiction or unresolved dimension remains.
7. Build each functional block in its own local coordinate system from the approved drawing. Keep base, holders, stands, cups, covers, and inserts separate when the user may move or replace them.
8. Assemble only through explicit Placement/Move transforms. Calculate rotated extents before accepting spacing or bed contact.
9. Make the intended print orientation support-aware:
   - connect every intended printed block to the bed or base;
   - fill the complete underside of shelves and ledges with wedges or gussets;
   - make support widths reach the shelf edges unless a cantilever is intentional;
   - cut cable paths after fusing all solids they must cross;
   - keep service openings accessible without trapped supports.
10. Export editable and manufacturing deliverables.
11. Validate the exported bytes and geometric invariants.
12. Regenerate final SVG and DXF projections from the completed 3D geometry. Compare both with the approved preliminary revision and resolve every mismatch before delivery.

## Pre-model drawing gate

- Use true orthographic projections, not a perspective render: front, top, and right side.
- Keep projection origins, scales, and corresponding edges aligned.
- Draw hidden edges or sections where pockets, channels, recesses, and internal supports cannot otherwise be verified.
- Dimension from the shared parameter table. Do not manually retype values into the drawing.
- Generate SVG and DXF from the same parameterized 2D geometry. Do not raster-trace the SVG or convert screen pixels into DXF units.
- Keep DXF model space at 1:1 in millimetres. Apply sheet scale only in a layout, viewport, or title annotation.
- Put visible outlines, hidden edges, centres, dimensions, and text on separate DXF layers.
- Mark each separately movable block and its intended final Placement.
- Include enough dimensions to reconstruct the model without guessing; avoid duplicating the same dimension in conflicting views.
- Treat user approval as the gate to 3D generation unless the user explicitly waives the intermediate review.
- Treat an approved preliminary drawing as the geometry contract. If later engineering constraints require a change, revise the drawing and revision mark before rebuilding the affected 3D blocks.

## CAD construction rules

- Put all editable values in one `parameters.json` (see [assets/parameters.example.json](assets/parameters.example.json) for the schema: `revision`, `units`, `nominal`, `clearances`, `derived`). Generate SVG, DXF, the FreeCAD/STEP model, and STL from that same file — never scatter unexplained literals through geometry code or retype values per deliverable.
- Express derived values as formulas when possible. Examples include rotated Z placement, wedge drop, clear slot size, and tool-pocket diameter.
- Separate nominal size from clearance. A 20 mm object and a 21 mm slot must remain two explainable parameters, not one magic number.
- Round user-facing edges deliberately. Parameterize plan radius, profile radius, and edge fillet separately because they solve different problems.
- Apply cuts for pockets, drainage, and cables after the relevant solids are united. A channel that only cuts the visible plate but not its shelf or support is incomplete.
- Preserve open access when requested. Removing side cheeks means deleting their solids, not merely hiding them in a drawing.
- Do not fuse logical assembly components in the editable STEP or FreeCAD model unless the user asks for one body. A print-ready STL may contain overlapping shells that the slicer unions.
- Never disguise a mesh as STEP. STEP must contain BREP geometry and named products/components.

## Tool and format selection

- Prefer native FreeCAD generation when `FreeCADCmd` or FreeCAD Python is available.
- When FreeCAD is unavailable, generate BREP/STEP with an OpenCascade-compatible kernel and provide a FreeCAD macro that rebuilds the same named blocks.
- Use `PartDesign::Feature` or equivalent named objects for blocks and `Placement` for final Move/Rotate assembly.
- Use SVG as the primary review drawing and render it for visual inspection before modelling.
- Use DXF as the mandatory editable engineering drawing. Preserve millimetres, 1:1 model-space geometry, named layers, line types, and editable text or dimensions where the selected DXF version permits them.
- Generate PDF only when the user requests a printable or archival sheet. PDF is not a substitute for SVG review or editable DXF.
- Deliver, when relevant:
  - FreeCAD macro or `.FCStd`;
  - named STEP assembly;
  - print-ready STL;
  - preliminary and final SVG drawings;
  - preliminary and final DXF drawings;
  - optional engineering PDF;
  - concise parameter/readme file.

Use [assets/freecad-parametric-template.FCMacro](assets/freecad-parametric-template.FCMacro) as a starting point when creating a FreeCAD macro from scratch.

## Validation gates

Do not deliver after only checking that files exist.

Run [scripts/validate_stl.py](scripts/validate_stl.py) on each print-ready STL. Assert expected size, bed plane, absence of vertices below the bed, and required bed-contact span when those values are known. Use `--empty-region` to prove that requested openings or removed walls are actually empty.

Run [scripts/validate_step.py](scripts/validate_step.py) on each STEP assembly. Require the STEP terminator, BREP solids, and every expected component name.

Run [scripts/validate_dxf.py](scripts/validate_dxf.py) on every DXF drawing. Require millimetre units, the expected layers, enough editable geometry, required view labels, and a valid `EOF` terminator.

Run [scripts/validate_projections.py](scripts/validate_projections.py) to compare the preliminary drawing against the final model-derived drawing (and, within one drawing, front/top/side against each other). Require matching X/Y/Z envelopes across view pairs and a matching revision mark.

Run [scripts/validate_manifest.py](scripts/validate_manifest.py) on the delivery `manifest.json`. Require every listed file to exist and its revision to match the approved drawing's revision.

Also verify task-specific invariants numerically. Typical checks:

- preliminary front, top, and side envelopes agree on every shared axis;
- SVG and DXF share the same nominal dimensions and revision;
- the final model-derived SVG and DXF projections match the approved preliminary drawing and revision;
- nearest-point clearance is at least the requested value;
- a tilted stand's minimum Z equals the top of the base;
- support contact spans the full shelf width;
- no mesh vertices lie below the print plane;
- a cable channel stays empty through plate, shelf, wedge, and base;
- open slot regions contain no triangle centroids above the base;
- STL byte count matches its triangle header;
- STEP contains named products rather than one anonymous accidental solid.

If a check fails, revise the geometry and regenerate every dependent deliverable. Do not patch only the drawing.

## Revision behavior

- Assign a new revision when geometry changes materially. Bump `revision` in `parameters.json` and keep every deliverable stamped with it.
- Carry unchanged parameters forward explicitly.
- Describe what changed and which former revision should not be printed.
- Re-export and revalidate STEP, STL, source, and drawing together.
- Generate a `manifest.json` (revision, units, approved drawing, and the source/STEP/STL filenames) alongside the deliverables so no file from a stale revision can be mistaken for current. Validate it with [scripts/validate_manifest.py](scripts/validate_manifest.py).
- Lead the handoff with the verified outcome and direct file links.

## Communication

- Explain geometric faults concretely: identify the transformed edge, conflicting volume, unsupported interval, or missing cut.
- Distinguish conceptual renders from CAD truth.
- When the user supplies a screenshot, acknowledge the visible failure and describe the exact solid or Placement change that will fix it.
- Avoid claiming “support-free” from appearance alone. Confirm bed contact and edge-to-edge support in the exported mesh.
