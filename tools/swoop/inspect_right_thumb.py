import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import math
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))

sw = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

mat_arm_to_mesh = sw.matrix_world.inverted() @ arm.matrix_world
rot_arm_to_mesh = mat_arm_to_mesh.to_3x3()

LEFT_FIST_QUATS = {
    'Bone_L_Finger0': (0.996808, 0.001097, -0.078611, -0.013909),
    'Bone_L_Finger01': (0.985, 0.0, 0.0, 0.174),
    'Bone_L_Finger02': (0.924, 0.0, 0.0, 0.383),
    'Bone_L_Finger1': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger11': (0.887, 0.0, 0.0, 0.462),
    'Bone_L_Finger12': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger2': (0.906, 0.0, 0.0, 0.423),
    'Bone_L_Finger21': (0.887, 0.0, 0.0, 0.462),
    'Bone_L_Finger22': (0.887, 0.0, 0.0, 0.462),
}

def pose_axis(bn, axis_mesh, rad):
    pb = arm.pose.bones[bn]
    bm = (rot_arm_to_mesh @ pb.bone.matrix_local.to_3x3()).normalized()
    la = (bm.inverted() @ axis_mesh.normalized()).normalized()
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion(la, rad)

# Apply exact Left hand quats, and mirror Left thumb axes across X=0 onto Right thumb!
for bn, qt in LEFT_FIST_QUATS.items():
    pb = arm.pose.bones[bn]
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion(qt).normalized()

    if "Finger0" in bn:
        q_l = Quaternion(qt).normalized()
        ax_local, angle = q_l.to_axis_angle()
        bm_l = (rot_arm_to_mesh @ pb.bone.matrix_local.to_3x3()).normalized()
        ax_mesh_l = (bm_l @ ax_local).normalized()
        # Mirror axial vector across X=0: (ax, ay, az) -> (-ax, ay, az) with -angle => (ax, -ay, -az) with +angle!
        ax_mesh_r = Vector((-ax_mesh_l.x, ax_mesh_l.y, ax_mesh_l.z)).normalized()
        rbn = bn.replace("Bone_L_", "Bone_R_")
        pose_axis(rbn, ax_mesh_r, -angle)
        print(f"Mirror {bn} -> {rbn}: L_ax_mesh={tuple(round(v,3) for v in ax_mesh_l)} ang={math.degrees(angle):+.1f} => R_ax_mesh={tuple(round(v,3) for v in ax_mesh_r)} ang={math.degrees(-angle):+.1f}")

for bn, deg in [("Bone_R_Finger1", 65), ("Bone_R_Finger11", 75), ("Bone_R_Finger12", 65),
                ("Bone_R_Finger2", 65), ("Bone_R_Finger21", 80), ("Bone_R_Finger22", 75)]:
    pose_axis(bn, Vector((0, -1, 0)), math.radians(deg))

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = sw.evaluated_get(deps).data

print("\n=== Mirrored L vs R Finger Centroids ===")
for side in ("L", "R"):
    for fn in ("Finger0", "Finger01", "Finger02", "Finger11", "Finger12", "Finger21", "Finger22"):
        vg = sw.vertex_groups.get(f"Bone_{side}_{fn}")
        pts = [ev.vertices[v.index].co for v in sw.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
        if pts:
            mc = sum(pts, Vector()) / len(pts)
            print(f"  Bone_{side}_{fn:8s}: mean=({mc.x:+.3f}, {mc.y:+.3f}, {mc.z:+.3f})")
