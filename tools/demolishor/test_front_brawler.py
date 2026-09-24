import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
for obj in list(bpy.data.objects):
    if obj != mesh:
        bpy.data.objects.remove(obj, do_unlink=True)

mesh.scale = (1.775, 1.775, 1.775)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)
mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)
min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# 1. Spread legs outward by 8.0 deg
angle = 8.0
rot_l = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Y')
rot_r = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Y')
rot_l_level = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Y')
rot_r_level = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Y')
rot_l_yaw = mathutils.Matrix.Rotation(math.radians(angle), 4, 'Z')
rot_r_yaw = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Z')

l_hip_pivot = mathutils.Vector((-0.85, -0.1, 4.8))
r_hip_pivot = mathutils.Vector((0.85, -0.1, 4.8))

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee"])]
l_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg03", "L_Leg04"])]
r_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg03", "R_Leg04"])]

for v in mesh.data.vertices:
    if any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups):
        v.co = l_hip_pivot + (rot_l @ (v.co - l_hip_pivot))
    elif any(g.group in r_leg_vgs and g.weight > 0.3 for g in v.groups):
        v.co = r_hip_pivot + (rot_r @ (v.co - r_hip_pivot))

l_foot_pts = [v.co for v in mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)]
if l_foot_pts:
    p = sum(l_foot_pts, mathutils.Vector((0, 0, 0))) / len(l_foot_pts)
    for v in mesh.data.vertices:
        if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups):
            v.co = p + (rot_l_yaw @ (rot_l_level @ (v.co - p)))

r_foot_pts = [v.co for v in mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups)]
if r_foot_pts:
    p = sum(r_foot_pts, mathutils.Vector((0, 0, 0))) / len(r_foot_pts)
    for v in mesh.data.vertices:
        if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups):
            v.co = p + (rot_r_yaw @ (rot_r_level @ (v.co - p)))

# 2. Forearms tilt forward by +18 deg
rot_forearm = mathutils.Matrix.Rotation(math.radians(18.0), 4, 'X')
l_elbow_pivot = mathutils.Vector((-3.26, -0.45, 6.50))
r_elbow_pivot = mathutils.Vector((3.35, -0.31, 6.52))

l_forearm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_forearm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

for v in mesh.data.vertices:
    if any(g.group in l_forearm_vgs and g.weight > 0.3 for g in v.groups):
        v.co = l_elbow_pivot + (rot_forearm @ (v.co - l_elbow_pivot))
    elif any(g.group in r_forearm_vgs and g.weight > 0.3 for g in v.groups):
        v.co = r_elbow_pivot + (rot_forearm @ (v.co - r_elbow_pivot))

# Re-ground boots
min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Render FRONT VIEW (Camera at +Y looking towards -Y)
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0, 18, 5.0)
cam_obj.rotation_euler = (math.radians(90), 0, math.radians(180))

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
light_data.energy = 4.0
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (0, 15, 12)
light_obj.rotation_euler = (math.radians(-60), 0, 0)

out_img = r"d:\Agent\tftf\tools\demolishor\preview_front_brawler.png"
bpy.context.scene.render.filepath = out_img
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered FRONT view to {out_img}")
