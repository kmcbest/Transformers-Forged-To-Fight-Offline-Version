import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector, Quaternion
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")
sym_ab = bpy.data.objects.get("Symbol_AB")

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon"] or o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

# Frame 1 of idle01
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

q_dict = {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones}
loc_dict = {pb.name: pb.location.copy() for pb in arm.pose.bones}
arm.animation_data_clear()

for pb in arm.pose.bones:
    pb.rotation_quaternion = q_dict[pb.name]
    pb.location = loc_dict[pb.name]

# Apply arm tweak
bip_lua = arm.pose.bones.get("Bip001 L UpperArm")
bip_lfa = arm.pose.bones.get("Bip001 L Forearm")
dq_ua = Quaternion(Vector((0, 0, 1)), math.radians(50)) @ Quaternion(Vector((1, 0, 0)), math.radians(10))
dq_fa = Quaternion(Vector((1, 0, 0)), math.radians(-10))
bip_lua.rotation_quaternion = q_dict["Bip001 L UpperArm"] @ dq_ua
bip_lfa.rotation_quaternion = q_dict["Bip001 L Forearm"] @ dq_fa

bpy.context.view_layer.update()

# Bake evaluated mesh for Swoop
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

baked_swoop = bpy.data.objects.new("cha_swoop_robot_baked", eval_mesh)
bpy.context.scene.collection.objects.link(baked_swoop)
baked_swoop.matrix_world = eval_obj.matrix_world

# Copy vertex groups
for vg in swoop.vertex_groups:
    baked_swoop.vertex_groups.new(name=vg.name)
    for v in swoop.data.vertices:
        for g in v.groups:
            if g.group == vg.index:
                baked_swoop.vertex_groups[vg.name].add([v.index], g.weight, 'REPLACE')

baked_swoop.parent = None
bpy.context.view_layer.objects.active = baked_swoop
bpy.ops.object.select_all(action='DESELECT')
baked_swoop.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

zs = [v.co.z for v in baked_swoop.data.vertices]
min_z = min(zs)
max_z = max(zs)
scale_factor = 11.40 / (max_z - min_z)
print(f"Scale factor: {scale_factor:.4f}")

for v in baked_swoop.data.vertices:
    v.co.x *= scale_factor
    v.co.y *= scale_factor
    v.co.z = (v.co.z - min_z) * scale_factor

def vg_mean_x(name):
    vg = baked_swoop.vertex_groups.get(name)
    if not vg: return None
    pts = [v.co.x for v in baked_swoop.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return sum(pts) / len(pts) if pts else None

print(f"Axis Audit:")
print(f"  Left Hand mean X:  {vg_mean_x('Bone_L_Hand'):+.3f}m (must be > +0.5)")
print(f"  Right Hand mean X: {vg_mean_x('Bone_R_Hand'):+.3f}m (must be < -0.5)")
print(f"  Left Arm mean X:   {vg_mean_x('Bone_L_UpperArm'):+.3f}m (must be > +0.5)")
print(f"  Right Arm mean X:  {vg_mean_x('Bone_R_UpperArm'):+.3f}m (must be < -0.5)")
print(f"  Left Foot mean X:  {vg_mean_x('Bone_L_Foot00'):+.3f}m (must be > +0.5)")
print(f"  Right Foot mean X: {vg_mean_x('Bone_R_Foot00'):+.3f}m (must be < -0.5)")

# Render front preview
mat = bpy.data.materials.new("M_Baked_Preview")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png")
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
baked_swoop.data.materials.append(mat)

arm.hide_render = True
swoop.hide_render = True
if sym_ab: sym_ab.hide_render = True

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0, -20, 5.7))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_baked_robot_tweaked.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_baked_robot_tweaked.png")
