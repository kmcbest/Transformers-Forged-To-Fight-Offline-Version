import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Ironhide
bpy.ops.wm.obj_import(filepath="tools/demolishor/ironhide_extracted/ironhide.obj")
ironhide = bpy.context.selected_objects[0]

# 2. Load Demolishor
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

# Scale by 1.775
scale = 1.775
mesh.scale = (scale, scale, scale)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)

# Test rotation 90 deg around Z
mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

verts = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]
print(f"Demolishor after +90 deg Z rotation:")
print(f"  X (width): {min(xs):.2f} to {max(xs):.2f} (span: {max(xs)-min(xs):.2f})")
print(f"  Y (depth): {min(ys):.2f} to {max(ys):.2f} (span: {max(ys)-min(ys):.2f})")
print(f"  Z (height): {min(zs):.2f} to {max(zs):.2f} (span: {max(zs)-min(zs):.2f})")

# Check where the Left Arm is in vertex groups
l_arm_vg = mesh.vertex_groups.get("L_Arm02_Shoulder_XB")
if l_arm_vg:
    l_arm_verts = [mesh.data.vertices[v.index].co for v in mesh.data.vertices for g in v.groups if g.group == l_arm_vg.index and g.weight > 0.5]
    if l_arm_verts:
        avg_x = sum(v.x for v in l_arm_verts) / len(l_arm_verts)
        avg_y = sum(v.y for v in l_arm_verts) / len(l_arm_verts)
        avg_z = sum(v.z for v in l_arm_verts) / len(l_arm_verts)
        print(f"  L_Arm avg pos: X={avg_x:.2f}, Y={avg_y:.2f}, Z={avg_z:.2f}")

r_arm_vg = mesh.vertex_groups.get("R_Arm02_Shoulder_XB")
if r_arm_vg:
    r_arm_verts = [mesh.data.vertices[v.index].co for v in mesh.data.vertices for g in v.groups if g.group == r_arm_vg.index and g.weight > 0.5]
    if r_arm_verts:
        avg_x = sum(v.x for v in r_arm_verts) / len(r_arm_verts)
        avg_y = sum(v.y for v in r_arm_verts) / len(r_arm_verts)
        avg_z = sum(v.z for v in r_arm_verts) / len(r_arm_verts)
        print(f"  R_Arm avg pos: X={avg_x:.2f}, Y={avg_y:.2f}, Z={avg_z:.2f}")
