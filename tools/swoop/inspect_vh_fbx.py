import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path("3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx").resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh_obj = None
arm_obj = None
for o in bpy.data.objects:
    if o.type == 'MESH':
        mesh_obj = o
    elif o.type == 'ARMATURE':
        arm_obj = o

print(f"Mesh: {mesh_obj.name if mesh_obj else 'None'}")
print(f"Armature: {arm_obj.name if arm_obj else 'None'}")

if mesh_obj:
    print(f"Vertex count: {len(mesh_obj.data.vertices)}")
    print(f"Vertex groups: {[vg.name for vg in mesh_obj.vertex_groups]}")
    # Check max weight per group
    vg_weights = {vg.name: 0 for vg in mesh_obj.vertex_groups}
    for v in mesh_obj.data.vertices:
        for g in v.groups:
            vg_name = mesh_obj.vertex_groups[g.group].name
            if g.weight > 0.01:
                vg_weights[vg_name] += 1
    for name, cnt in sorted(vg_weights.items(), key=lambda x: -x[1]):
        print(f"  {name}: {cnt} vertices")
