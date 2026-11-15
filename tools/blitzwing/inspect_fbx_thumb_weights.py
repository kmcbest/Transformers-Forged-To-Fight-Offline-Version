import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_robot.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm_obj = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]

print(f"Loaded FBX: {mesh_obj.name}, verts={len(mesh_obj.data.vertices)}")

for side in ['Left', 'Right']:
    print(f"\n=== {side} Hand Thumb Vertices ===")
    for t_idx in [1, 2, 3]:
        vg_name = f"{side}HandThumb{t_idx}"
        if vg_name in mesh_obj.vertex_groups:
            vg = mesh_obj.vertex_groups[vg_name]
            verts_in_vg = []
            for v in mesh_obj.data.vertices:
                for g in v.groups:
                    if g.group == vg.index and g.weight > 0.05:
                        verts_in_vg.append((v, g.weight))
            print(f"  {vg_name}: {len(verts_in_vg)} vertices")
            if verts_in_vg:
                centroid = sum((v.co * w for v, w in verts_in_vg), Vector((0,0,0))) / sum(w for v, w in verts_in_vg)
                u_cent = (-centroid.x, centroid.z, -centroid.y)
                print(f"    Centroid (Blender): ({centroid.x:.3f}, {centroid.y:.3f}, {centroid.z:.3f})")
                print(f"    Centroid (Unity):   ({u_cent[0]:.3f}, {u_cent[1]:.3f}, {u_cent[2]:.3f})")

print("\n=== Armature Thumb Bones in Rest Pose ===")
for side in ['Left', 'Right']:
    for t_idx in [1, 2, 3]:
        bname = f"{side}HandThumb{t_idx}"
        bone = arm_obj.data.bones.get(bname)
        if bone:
            print(f"  {bname}: head=({bone.head_local.x:.3f}, {bone.head_local.y:.3f}, {bone.head_local.z:.3f}), tail=({bone.tail_local.x:.3f}, {bone.tail_local.y:.3f}, {bone.tail_local.z:.3f}), len={bone.length:.4f}")
