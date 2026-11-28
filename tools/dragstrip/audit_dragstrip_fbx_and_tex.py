import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from pathlib import Path

FBX_PATH = Path(r"E:\Agent\TFTF-blender\3rd-party-models\DragStrip\source\source\Dragstrip.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

print("=== Dragstrip.fbx Objects ===")
for o in bpy.data.objects:
    print(f"  OBJ: {o.name:28s} type={o.type:8s} parent={o.parent.name if o.parent else None}")
    if o.type == 'MESH':
        mats = [m.name for m in o.data.materials]
        xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]; zs = [v.co.z for v in o.data.vertices]
        print(f"       verts={len(o.data.vertices)} polys={len(o.data.polygons)} vgs={len(o.vertex_groups)} mats={mats}")
        print(f"       local bounds: X=[{min(xs):.4f},{max(xs):.4f}] Y=[{min(ys):.4f},{max(ys):.4f}] Z=[{min(zs):.4f},{max(zs):.4f}]")
        if o.data.uv_layers:
            uvd = o.data.uv_layers.active.data
            us = [d.uv.x for d in uvd]; vs = [d.uv.y for d in uvd]
            print(f"       UV '{o.data.uv_layers.active.name}': U=[{min(us):.3f},{max(us):.3f}] V=[{min(vs):.3f},{max(vs):.3f}]")
        if len(o.vertex_groups) > 0:
            print(f"       VGs: {[g.name for g in o.vertex_groups]}")

print("\n=== Dragstrip.fbx Actions ===")
for a in bpy.data.actions:
    print(f"  ACT: {a.name:48s} [{a.frame_range[0]:.1f}, {a.frame_range[1]:.1f}]")

# Also save UV triangle coordinates per mesh to JSON for Python UV rasterizer!
import json
uv_tris = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and o.data.uv_layers and "Dragstrip" in o.name:
        uvd = o.data.uv_layers.active.data
        tris = []
        for p in o.data.polygons:
            ls = p.loop_indices
            pts = [[float(uvd[i].uv.x), float(uvd[i].uv.y)] for i in ls]
            if len(pts) == 3:
                tris.append(pts)
            elif len(pts) == 4:
                tris.append([pts[0], pts[1], pts[2]])
                tris.append([pts[0], pts[2], pts[3]])
        uv_tris[o.name] = tris
Path(r"E:\Agent\TFTF-blender\scratch\dragstrip_uv_tris.json").write_text(json.dumps(uv_tris), encoding="utf-8")
print("[✓] Saved dragstrip_uv_tris.json")
