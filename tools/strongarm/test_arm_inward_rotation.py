import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils

fbx_path = r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if orig_arm.animation_data:
    orig_arm.animation_data_clear()
orig_arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for m in list(mesh_objs):
    if m.name in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
        bpy.data.objects.remove(m, do_unlink=True)
        mesh_objs.remove(m)

for m in mesh_objs:
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    for mod in list(m.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    m.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.data.objects.remove(orig_arm, do_unlink=True)

# Arm submeshes
left_arm_objs = [
    "bot:shoulderInner_geo_L", "bot:shoulderRim_geo_L", "bot:shoulderTire_geo_L",
    "bot:wheelDeco_geo_L", "bot:fender_geo_L", "bot:elbowJointA_geo_L",
    "bot:arm_geo_L", "bot:elbow_geo_L", "bot:elbowJointB_geo_L",
    "bot:topLight_geo_L", "bot:hand_geo_L", "bot:palm_geo_L"
]
right_arm_objs = [
    "bot:shoulderInner_geo_R", "bot:shoulderRim_geo_R", "bot:shoulderTire_geo_R",
    "bot:wheelDeco_geo_R", "bot:fender_geo_R", "bot:elbowJointA_geo_R",
    "bot:arm_geo_R", "bot:elbow_geo_R", "bot:elbowJointB_geo_R",
    "bot:topLight_geo_R", "bot:hand_geo_R", "bot:palm_geo_R"
]

# Find shoulder pivot (shoulderBall center)
sb_l = bpy.data.objects["bot:shoulderBall_geo_L"]
sb_r = bpy.data.objects["bot:shoulderBall_geo_R"]
piv_l = mathutils.Vector(sum((v.co for v in sb_l.data.vertices), mathutils.Vector()) / len(sb_l.data.vertices))
piv_r = mathutils.Vector(sum((v.co for v in sb_r.data.vertices), mathutils.Vector()) / len(sb_r.data.vertices))
print(f"Shoulder pivot Left (raw FBX):  ({piv_l.x:.4f}, {piv_l.y:.4f}, {piv_l.z:.4f})")
print(f"Shoulder pivot Right (raw FBX): ({piv_r.x:.4f}, {piv_r.y:.4f}, {piv_r.z:.4f})")

# In raw FBX: Y is Up, X is Left/Right, Z is Forward/Back
# To rotate arms inward towards the body in the coronal plane (X-Y plane):
# Around Z axis!
# For Left arm (at X > 0 in raw FBX): rotating clockwise (negative Z) brings X closer to 0 (body)
# For Right arm (at X < 0 in raw FBX): rotating counter-clockwise (positive Z) brings X closer to 0 (body)
rot_angle_deg = 32.0 # degrees inward
rot_rad = math.radians(rot_angle_deg)

# Rotate left arm parts
R_l = mathutils.Matrix.Rotation(-rot_rad, 4, 'Z')
T_l = mathutils.Matrix.Translation(piv_l)
T_l_inv = mathutils.Matrix.Translation(-piv_l)
M_l = T_l @ R_l @ T_l_inv

for name in left_arm_objs:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co = M_l @ v.co
        o.data.update()

# Rotate right arm parts
R_r = mathutils.Matrix.Rotation(rot_rad, 4, 'Z')
T_r = mathutils.Matrix.Translation(piv_r)
T_r_inv = mathutils.Matrix.Translation(-piv_r)
M_r = T_r @ R_r @ T_r_inv

for name in right_arm_objs:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co = M_r @ v.co
        o.data.update()

# Now check new hand positions
palm_l = bpy.data.objects["bot:palm_geo_L"]
palm_r = bpy.data.objects["bot:palm_geo_R"]
p_l_mean = sum((v.co for v in palm_l.data.vertices), mathutils.Vector()) / len(palm_l.data.vertices)
p_r_mean = sum((v.co for v in palm_r.data.vertices), mathutils.Vector()) / len(palm_r.data.vertices)

all_verts_y = [v.co.y for m in mesh_objs for v in m.data.vertices]
raw_height = max(all_verts_y) - min(all_verts_y)
scale_factor = 9.3040 / raw_height
min_y = min(all_verts_y)

ux_l = -p_l_mean.x * scale_factor
uy_l = (p_l_mean.y - min_y) * scale_factor
ux_r = -p_r_mean.x * scale_factor
uy_r = (p_r_mean.y - min_y) * scale_factor

print(f"\nAfter {rot_angle_deg} deg inward rotation:")
print(f"Left Hand in Unity:  X={ux_l:.3f}, Y={uy_l:.3f} (Prowl target: X=-2.057, Y=4.597)")
print(f"Right Hand in Unity: X={ux_r:.3f}, Y={uy_r:.3f} (Prowl target: X=+2.057, Y=4.597)")
