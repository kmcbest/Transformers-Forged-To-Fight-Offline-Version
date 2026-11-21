import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")
sym_ab = bpy.data.objects.get("Symbol_AB")

# Evaluate at idle01 frame 1
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Bake evaluated mesh for Swoop.001
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

# Create new baked object
baked_swoop = bpy.data.objects.new("cha_swoop_robot_baked", eval_mesh)
bpy.context.scene.collection.objects.link(baked_swoop)
# Copy matrix world from evaluated object
baked_swoop.matrix_world = eval_obj.matrix_world

# Copy vertex groups
for vg in swoop.vertex_groups:
    baked_swoop.vertex_groups.new(name=vg.name)
    # Check weights on vertices
    for v in swoop.data.vertices:
        for g in v.groups:
            if g.group == vg.index:
                baked_swoop.vertex_groups[vg.name].add([v.index], g.weight, 'REPLACE')

# Unparent and apply transform
baked_swoop.parent = None
bpy.context.view_layer.objects.active = baked_swoop
bpy.ops.object.select_all(action='DESELECT')
baked_swoop.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Measure baked height
zs = [v.co.z for v in baked_swoop.data.vertices]
min_z = min(zs)
max_z = max(zs)
baked_h = max_z - min_z
print(f"Baked Swoop height: {baked_h:.4f}m (min_z={min_z:.4f}, max_z={max_z:.4f})")

# Target height for Ramjet is ~11.40m
scale_factor = 11.40 / baked_h
print(f"Required scale factor: {scale_factor:.4f}")

# Scale and ground
for v in baked_swoop.data.vertices:
    v.co.x *= scale_factor
    v.co.y *= scale_factor
    v.co.z = (v.co.z - min_z) * scale_factor

new_xs = [v.co.x for v in baked_swoop.data.vertices]
new_ys = [v.co.y for v in baked_swoop.data.vertices]
new_zs = [v.co.z for v in baked_swoop.data.vertices]
print(f"Scaled & Grounded Swoop Robot:")
print(f"  X bounds: [{min(new_xs):.3f}, {max(new_xs):.3f}] (span: {max(new_xs)-min(new_xs):.3f}m)")
print(f"  Y bounds: [{min(new_ys):.3f}, {max(new_ys):.3f}] (span: {max(new_ys)-min(new_ys):.3f}m)")
print(f"  Z bounds: [{min(new_zs):.3f}, {max(new_zs):.3f}] (span: {max(new_zs)-min(new_zs):.3f}m)")

# Audit Left / Right axis:
def vg_mean_x(name):
    vg = baked_swoop.vertex_groups.get(name)
    if not vg: return None
    pts = [v.co.x for v in baked_swoop.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return sum(pts) / len(pts) if pts else None

print(f"Left Hand mean X:  {vg_mean_x('Bone_L_Hand'):+.3f}m (must be > +0.5)")
print(f"Right Hand mean X: {vg_mean_x('Bone_R_Hand'):+.3f}m (must be < -0.5)")
print(f"Left Arm mean X:   {vg_mean_x('Bone_L_UpperArm'):+.3f}m (must be > +0.5)")
print(f"Right Arm mean X:  {vg_mean_x('Bone_R_UpperArm'):+.3f}m (must be < -0.5)")
print(f"Left Foot mean X:  {vg_mean_x('Bone_L_Foot00'):+.3f}m (must be > +0.5)")
print(f"Right Foot mean X: {vg_mean_x('Bone_R_Foot00'):+.3f}m (must be < -0.5)")

# Render front view of baked robot
mat = bpy.data.materials.new("M_Baked_Preview")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png")
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
baked_swoop.data.materials.append(mat)

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
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_baked_robot_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_baked_robot_preview.png")
