import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
scale_factor = 1.775
mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)
mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Test leg spread angles
# Let's test 10 degrees outward spread
angle_deg = 10.0
rot_l_leg = mathutils.Matrix.Rotation(math.radians(angle_deg), 4, 'Y')
rot_r_leg = mathutils.Matrix.Rotation(math.radians(-angle_deg), 4, 'Y')

# Counter-rotate foot so tread sole stays flat on ground
rot_l_foot_level = mathutils.Matrix.Rotation(math.radians(-angle_deg), 4, 'Y')
rot_r_foot_level = mathutils.Matrix.Rotation(math.radians(angle_deg), 4, 'Y')

# Outward toe flare
rot_l_foot_yaw = mathutils.Matrix.Rotation(math.radians(10.0), 4, 'Z')
rot_r_foot_yaw = mathutils.Matrix.Rotation(math.radians(-10.0), 4, 'Z')

l_hip_pivot = mathutils.Vector((-0.85, -0.1, 4.8))
r_hip_pivot = mathutils.Vector((0.85, -0.1, 4.8))

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee"])]

l_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg03", "L_Leg04"])]
r_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg03", "R_Leg04"])]

# Apply rotation to Left Leg
for v in mesh.data.vertices:
    # Check if in left leg
    is_l_leg = any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups)
    is_l_foot = any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)
    
    if is_l_leg:
        # Tilt around hip
        rel = v.co - l_hip_pivot
        v.co = l_hip_pivot + (rot_l_leg @ rel)

# Level left foot and flare toe
# Find new foot center
l_foot_pts = [v.co for v in mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)]
if l_foot_pts:
    l_foot_pivot = sum(l_foot_pts, mathutils.Vector((0, 0, 0))) / len(l_foot_pts)
    for v in mesh.data.vertices:
        if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups):
            rel = v.co - l_foot_pivot
            # Level and yaw
            v.co = l_foot_pivot + (rot_l_foot_yaw @ (rot_l_foot_level @ rel))

# Apply rotation to Right Leg
for v in mesh.data.vertices:
    is_r_leg = any(g.group in r_leg_vgs and g.weight > 0.3 for g in v.groups)
    if is_r_leg:
        rel = v.co - r_hip_pivot
        v.co = r_hip_pivot + (rot_r_leg @ rel)

r_foot_pts = [v.co for v in mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups)]
if r_foot_pts:
    r_foot_pivot = sum(r_foot_pts, mathutils.Vector((0, 0, 0))) / len(r_foot_pts)
    for v in mesh.data.vertices:
        if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups):
            rel = v.co - r_foot_pivot
            v.co = r_foot_pivot + (rot_r_foot_yaw @ (rot_r_foot_level @ rel))

# Re-ground to Z = 0
min_z_after = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z_after
bpy.ops.object.transform_apply(location=True)

# Measure new feet bounds
l_foot_pts_after = [v.co for v in mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)]
r_foot_pts_after = [v.co for v in mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups)]
xs_l = [p.x for p in l_foot_pts_after]
xs_r = [p.x for p in r_foot_pts_after]
print(f"New Left Foot : X=[{min(xs_l):.2f}, {max(xs_l):.2f}], Center X={sum(xs_l)/len(xs_l):.2f}")
print(f"New Right Foot: X=[{min(xs_r):.2f}, {max(xs_r):.2f}], Center X={sum(xs_r)/len(xs_r):.2f}")
print(f"Inter-foot gap: {min(xs_r) - max(xs_l):.2f} meters!")

# Render preview
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0, -18, 5.0)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
light_data.energy = 4.0
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (0, -15, 12)
light_obj.rotation_euler = (math.radians(60), 0, 0)

out_img = r"d:\Agent\tftf\tools\demolishor\preview_wide_stance.png"
bpy.context.scene.render.filepath = out_img
bpy.context.scene.render.resolution_x = 960
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered wide stance preview to {out_img}")
