import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector

FBX_SRC = Path("3rd-party-models/swoop/01_master/Swoop_pbr.fbx").resolve()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

mesh = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")

print("=== Swoop.001 Vertex Groups on Arm/Shoulder/Hand ===")
for vg in mesh.vertex_groups:
    if any(k in vg.name.lower() for k in ["arm", "clav", "shoulder", "hand", "finger"]):
        # Count vertices with weight > 0.1
        cnt = sum(1 for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.1 for g in v.groups))
        print(f"  VG: {vg.name} (verts: {cnt})")

print("\n=== Armature Bones in Bip001 ===")
for b in arm.data.bones:
    if any(k in b.name.lower() for k in ["arm", "clav", "shoulder", "hand", "finger"]):
        print(f"  Bone: {b.name}, parent={b.parent.name if b.parent else None}, head={b.head_local}")

print("\n=== Actions in FBX ===")
for act in bpy.data.actions:
    print(f"  Action: {act.name}")
