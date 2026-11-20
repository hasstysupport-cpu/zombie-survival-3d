# City District 01

Static environment asset for the zombie-survival game, built procedurally with
Blender 5 (bpy) and exported to GLB.

## Files

- `assets/models/environment/city_district_01.glb` — game-ready (single merged mesh)
- `assets/models/environment/city_district_01.blend` — source scene
- `assets/models/environment/city_district_01.glb` validated with glTF-Transform (glTF 2.0, no errors)
- `specs/environment/city_district_01.json` — dimensions, landmarks, collision notes
- `tools/blender/build_city.py` — generator (deterministic, `random.seed(7)`)
- `tools/blender/render_city_previews.py` — preview renderer with distance fog

## Layout

- 300 x 300 m district, 5x5 blocks (BLOCK=36 m, STREET_W=8 m, PITCH=44 m), +Z up
- streets with lane markings + crosswalks, sidewalks everywhere
- 9 enterable buildings (door gaps kept clear, interior floor + furniture)
- landmarks: plaza/fountain (spawn, 0,0), hospital (0,78), cinema (0,-98),
  church tower (-4,-92), gas station (-90,2), radio tower (44,44)
- street props: 16 cars (2 flipped), 4 jersey barricades, 26 sandbags, 4 dumpsers,
  cones, 40 streetlights (emissive), fence rings
- 30,620 tris / 2,297 merged objects / 30 materials (3 emissive) — cheap enough for real-time

## Preview rendering pipeline (Blender 5 headless notes)

- World Volume Scatter renders black in headless Blender 5 Cycles — do not use.
- The modular compositor (`scene.compositing_node_group`) replaces the output with
  black in this bpy build; `CompositorNodeComposite`/`MixRGB` node types are gone and
  `OPEN_EXR_MULTILAYER` is unavailable, so passes cannot be extracted via compositor.
- Solution: render the plain bright PNG (sun 5.0 + bright sky background, Standard
  transform, exposure 0.6), then ray-cast per-pixel depth with `BVHTree.FromObject`
  and apply quadratic mist in numpy: `f = clamp((d-start)/depth, 0, 1) ** 2`.
- Per-shot fog range: aerial (40,260), street (4,70), landmarks (6-12, 60-110).

## Integration notes (three.js)

- Fog: `scene.fog = new THREE.FogExp2(0xbac6d1, 0.004-0.012)` (tune per area).
- Collision: trimesh/octree on `CityStatic`; cars/barricades/fences are blockers.
- Player spawn: plaza fountain at (0, -6, 0); survivor is 1.82 m (door 2.2 m) — scale OK.
