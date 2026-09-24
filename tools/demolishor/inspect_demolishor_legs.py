import bpy
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

# Ground feet
min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

for side, prefix in [("Left", "L_"), ("Right", "R_")]:
    leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in [f"{prefix}Leg", f"{prefix}Thigh", f"{prefix}Knee"])]
    leg_verts = [v.co for v in mesh.data.vertices for g in v.groups if g.group in leg_vgs and g.weight > 0.3]
    foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in [f"{prefix}Leg03", f"{prefix}Leg04"])]
    foot_verts = [v.co for v in mesh.data.vertices for g in v.groups if g.group in foot_vgs and g.weight > 0.3]
    
    xs_leg = [v.x for v in leg_verts]
    xs_foot = [v.x for v in foot_verts]
    ys_foot = [v.y for v in foot_verts]
    zs_foot = [v.z for v in foot_verts]
    print(f"Demolishor {side} Leg : X=[{min(xs_leg):.2f}, {max(xs_leg):.2f}], Center X={sum(xs_leg)/len(xs_leg):.2f}")
    print(f"Demolishor {side} Foot: X=[{min(xs_foot):.2f}, {max(xs_foot):.2f}], Center X={sum(xs_foot)/len(xs_foot):.2f}")
    print(f"Demolishor {side} Foot Y (depth): [{min(ys_foot):.2f}, {max(ys_foot):.2f}], Z (height): [{min(zs_foot):.2f}, {max(zs_foot):.2f}]")
