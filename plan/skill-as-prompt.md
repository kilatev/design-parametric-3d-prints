3D print part design. Order:

Base: ask the user for this skill's repo root path, call it $BASE. Prefix every script path below with it — do not cd.

1. params.json: nominal, clearances, derived(formulas), instances. Rev num. No stray numbers elsewhere.
2. Draw front/top/side SVG+DXF from params. mm, 1:1, layers(outline/hidden/centre/dim/text).
3. Check: $BASE/scripts/validate_dxf.py DXF --expect-layer L --min-geometry N
4. Show SVG. Wait user OK before 3D. Skip wait only if told.
5. Model each block separate solid own coords. Repeats: one model + instances[] + Placement. No hand-copy.
6. Join blocks only via Placement/Move. Check rotated bbox for bed fit/spacing.
7. Support rules: every block touch bed. Fill shelf underside (wedge). Support full shelf width. Cut channels after union. Keep openings clear.
8. Export: FreeCAD macro/.FCStd, STEP(named parts, BREP, unfused), STL, manifest.json(rev,files).
9. Check exports:
 - $BASE/scripts/validate_step.py STEP --expect-product NAME --min-solids N
 - $BASE/scripts/validate_stl.py STL --bed-z Z --expect-size WxHxD --min-contact-x X --min-contact-y Y --empty-region "x0,y0,z0,x1,y1,z1" --bed-size WxD --max-overhang DEG (angle check only, still eyeball it)
 - $BASE/scripts/estimate_material.py STL --density G (rough weight/filament, not slicer-exact)
10. Rebuild SVG+DXF from final 3D. Diff: $BASE/scripts/validate_projections.py pre.dxf final.dxf --tolerance T. Fix all mismatch.
11. Geometry change → bump rev. $BASE/scripts/diff_parameters.py old.json new.json → changelog from that output. Re-export+recheck all. $BASE/scripts/validate_manifest.py manifest.json --expect-revision R.

Don't: fuse STEP parts (STL can overlap, ok). Call it support-free by eye (only mesh bed-contact proves it). Chamfer non-visible edges. Patch only drawing on fail — fix geometry, redo all files.
