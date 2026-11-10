import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = bpy.data.objects["cha_prowl_gs_deluxe2016_00"]
arm = bpy.data.objects["character_model"]

for group_name in ["LeftLeg", "RightLeg", "LeftShoulder", "RightShoulder"]:
    vg = mesh.vertex_groups.get(group_name)
    bone = arm.data.bones.get(group_name)
    b_pos = arm.matrix_world @ bone.head_local
    strays = []
    for v in mesh.data.vertices:
        for g in v.groups:
            if g.group == vg.index and g.weight > 0.5:
                d = (v.co - b_pos).length
                if d > 2.5:
                    strays.append(v)
    print(f"\nGroup {group_name}: {len(strays)} stray vertices (Bone head: {b_pos.x:.2f}, {b_pos.y:.2f}, {b_pos.z:.2f})")
    if strays:
        min_x = min(v.co.x for v in strays)
        max_x = max(v.co.x for v in strays)
        min_y = min(v.co.y for v in strays)
        max_y = max(v.co.y for v in strays)
        min_z = min(v.co.z for v in strays)
        max_z = max(v.co.z for v in strays)
        print(f"  Stray bounds: X=[{min_x:.2f}, {max_x:.2f}], Y=[{min_y:.2f}, {max_y:.2f}], Z=[{min_z:.2f}, {max_z:.2f}]")
