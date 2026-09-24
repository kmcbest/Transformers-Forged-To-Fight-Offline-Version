import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
scale_factor = 1.85
mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)
mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

# Ground feet to Z=0
min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

print("Demolishor Bounding Box (Grounded to Z=0):")
print(f"X: [{min(v.co.x for v in mesh.data.vertices):.3f}, {max(v.co.x for v in mesh.data.vertices):.3f}]")
print(f"Y: [{min(v.co.y for v in mesh.data.vertices):.3f}, {max(v.co.y for v in mesh.data.vertices):.3f}]")
print(f"Z: [{min(v.co.z for v in mesh.data.vertices):.3f}, {max(v.co.z for v in mesh.data.vertices):.3f}]")

groups_to_check = [
    "C_Spine00_Hips_XB", "C_Spine02_Lumbar02_XB", "C_Head01_Face_XF2",
    "L_Leg01_Thigh_XB", "L_Leg02_Knee_XB", "L_Leg03_Ankle_XB",
    "R_Leg01_Thigh_XB", "R_Leg02_Knee_XB", "R_Leg03_Ankle_XB",
    "L_Arm02_Shoulder_XB", "L_Arm03_Elbow_XB", "L_Arm04_Hand_XB",
    "R_Arm02_Shoulder_XB", "R_Arm03_Elbow_XB", "R_Arm04_Hand_XB"
]

for gname in groups_to_check:
    vg = mesh.vertex_groups.get(gname)
    if vg:
        pts = [v.co for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.3]
        if pts:
            avg = sum(pts, mathutils.Vector((0, 0, 0))) / len(pts)
            print(f"{gname:25s}: count={len(pts):4d}, avg=({avg.x:6.2f}, {avg.y:6.2f}, {avg.z:6.2f})")
