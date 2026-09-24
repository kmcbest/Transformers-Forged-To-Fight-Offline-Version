import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"

for angle in [5.0, 7.0, 8.5, 10.0]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
    mesh.scale = (1.775, 1.775, 1.775)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.transform_apply(scale=True)
    mesh.rotation_euler = (0, 0, math.radians(90))
    bpy.ops.object.transform_apply(rotation=True)
    min_z = min(v.co.z for v in mesh.data.vertices)
    mesh.location.z -= min_z
    bpy.ops.object.transform_apply(location=True)

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

    xs_l = [v.co.x for v in mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.3 for g in v.groups)]
    xs_r = [v.co.x for v in mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.3 for g in v.groups)]
    gap = min(xs_r) - max(xs_l)
    span = max(xs_r) - min(xs_l)
    print(f"Angle {angle:4.1f} deg: Gap={gap:.2f}m, Span={span:.2f}m, L_Foot=[{min(xs_l):.2f}, {max(xs_l):.2f}], R_Foot=[{min(xs_r):.2f}, {max(xs_r):.2f}]")
