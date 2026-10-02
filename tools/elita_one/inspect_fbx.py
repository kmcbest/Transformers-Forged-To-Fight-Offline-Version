import bpy
import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

print("=== FBX Objects ===")
for obj in bpy.data.objects:
    print(f"Object: {obj.name}, Type: {obj.type}, Parent: {obj.parent.name if obj.parent else None}")

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
arm_objs = [o for o in bpy.data.objects if o.type == 'ARMATURE']

for m in mesh_objs:
    print(f"\nMesh: {m.name}, Verts: {len(m.data.vertices)}, Polys: {len(m.data.polygons)}")
    print(f"Vertex Groups count: {len(m.vertex_groups)}")
    for vg in m.vertex_groups:
        # find how many vertices have weight in this vg
        vcount = sum(1 for v in m.data.vertices if any(g.group == vg.index and g.weight > 0.001 for g in v.groups))
        if "wheel" in vg.name.lower() or "weapon" in vg.name.lower() or "socket" in vg.name.lower() or "piston" in vg.name.lower():
            print(f"  VG {vg.name}: {vcount} verts")

for a in arm_objs:
    print(f"\nArmature: {a.name}, Bones count: {len(a.data.bones)}")
    for b in a.data.bones:
        if b.parent is None:
            print(f"  Root bone: {b.name}")
