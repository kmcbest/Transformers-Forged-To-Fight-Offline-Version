import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Quaternion, Vector

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Clear animation data on arm so all bones are in pure Rest Pose
arm.animation_data_clear()

# Reset all pose bones to rest
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# Let's check finger rotations in Rest Pose
print("Rest Pose check: Bip001 L Hand rot:", arm.pose.bones["Bip001 L Hand"].rotation_quaternion)

# Now apply finger curling rotations
finger_quats = {
    'Bone_L_Finger0': (0.996808, 0.001097, -0.078611, -0.013909),
    'Bone_L_Finger01': (0.997442, -0.000001, 0.000000, 0.071480),
    'Bone_L_Finger02': (0.979345, -0.000001, -0.000001, 0.202198),
    'Bone_L_Finger1': (0.930682, -0.002064, -0.000110, 0.365824),
    'Bone_L_Finger11': (0.932585, -0.000141, -0.000004, 0.360950),
    'Bone_L_Finger12': (0.918953, 0.000194, -0.000036, 0.394366),
    'Bone_L_Finger2': (0.932293, -0.002034, -0.000154, 0.361697),
    'Bone_L_Finger21': (0.907342, 0.000050, 0.000003, 0.420392),
    'Bone_L_Finger22': (0.886585, -0.000000, 0.000000, 0.462565),
    'Bone_R_Finger0': (0.997871, 0.053770, -0.036849, 0.001986),
    'Bone_R_Finger01': (0.998401, 0.000000, 0.000000, 0.056523),
    'Bone_R_Finger02': (0.996362, 0.000000, -0.000000, 0.085221),
    'Bone_R_Finger1': (0.947818, -0.001720, -0.000150, 0.318807),
    'Bone_R_Finger11': (0.946067, 0.000130, -0.000000, 0.323972),
    'Bone_R_Finger12': (0.977746, 0.000027, -0.000005, 0.209792),
    'Bone_R_Finger2': (0.911139, -0.002332, -0.000189, 0.412092),
    'Bone_R_Finger21': (0.909270, 0.000092, 0.000001, 0.416206),
    'Bone_R_Finger22': (0.898111, -0.000071, -0.000001, 0.439770),
}

for bname, q in finger_quats.items():
    pb = arm.pose.bones.get(bname)
    if pb:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion(q)

bpy.ops.object.mode_set(mode='OBJECT')

# Evaluate mesh with armature modifier
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

print(f"Eval mesh vertices: {len(eval_mesh.vertices)}")

# Let's inspect bounds of finger vertices in raw mesh vs eval mesh
for side in ["L", "R"]:
    vg = mesh.vertex_groups.get(f"Bone_{side}_Finger12")
    pts_raw = [mesh.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    pts_curled = [eval_mesh.vertices[v.index].co for v in eval_mesh.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    print(f"--- Side {side} Finger12 (Fingertips) ---")
    print(f"  Raw Z: [{min(p.z for p in pts_raw):.4f}, {max(p.z for p in pts_raw):.4f}]")
    print(f"  Curled Z: [{min(p.z for p in pts_curled):.4f}, {max(p.z for p in pts_curled):.4f}]")
    print(f"  Raw Y: [{min(p.y for p in pts_raw):.4f}, {max(p.y for p in pts_raw):.4f}]")
    print(f"  Curled Y: [{min(p.y for p in pts_curled):.4f}, {max(p.y for p in pts_curled):.4f}]")

# Check non-finger vertices (e.g. Head, Spine, Thigh) to ensure ZERO change
for test_vg in ["Bip001 Head", "Bone_Spine1", "Bone_L_Thigh"]:
    vg = mesh.vertex_groups.get(test_vg)
    if vg:
        pts_raw = [mesh.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
        pts_curled = [eval_mesh.vertices[v.index].co for v in eval_mesh.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
        diff = max((p1 - p2).length for p1, p2 in zip(pts_raw, pts_curled))
        print(f"Non-finger VG {test_vg}: max diff = {diff:.6f}m (must be 0.000000)")
