import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

# 1. Inspect Blitzwing FBX
fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_obj = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

print("=== BLITZWING FBX THUMB MESH INSPECTION ===")
for side in ['Left', 'Right']:
    print(f"\n--- {side} Hand ---")
    for t_idx in [1, 2, 3]:
        vg_name = f"{side}HandThumb{t_idx}"
        vg = mesh_obj.vertex_groups.get(vg_name)
        bone = arm_obj.data.bones.get(vg_name)
        if vg and bone:
            verts = [v.co for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
            if verts:
                centroid = sum(verts, Vector((0,0,0))) / len(verts)
                # Offset from bone head
                offset_from_head = centroid - bone.head_local
                print(f"  {vg_name} ({len(verts)} verts):")
                print(f"    Bone Head:     ({bone.head_local.x:.3f}, {bone.head_local.y:.3f}, {bone.head_local.z:.3f})")
                print(f"    Vert Centroid: ({centroid.x:.3f}, {centroid.y:.3f}, {centroid.z:.3f})")
                print(f"    Offset:        ({offset_from_head.x:.3f}, {offset_from_head.y:.3f}, {offset_from_head.z:.3f})")
