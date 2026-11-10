import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh = bpy.data.objects["cha_prowl_gs_deluxe2016_00"]
arm = bpy.data.objects["character_model"]

# Check which vertex groups have vertices far from the bone
for vg in mesh.vertex_groups:
    v_indices = [v.index for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    if not v_indices:
        continue
    # Bone position
    bone = arm.data.bones.get(vg.name)
    if not bone:
        print(f"WARNING: Vertex group {vg.name} has no bone in armature!")
        continue
    b_pos = bone.head_local
    # Max distance of vertices in this group from bone head
    dists = [(mesh.data.vertices[i].co - b_pos).length for i in v_indices]
    max_d = max(dists)
    if max_d > 2.5: # More than 2.5 meters away from bone
        print(f"Group {vg.name:20s}: {len(v_indices):5d} verts, max dist={max_d:.2f}m (Bone at {b_pos.x:.2f}, {b_pos.y:.2f}, {b_pos.z:.2f})")
