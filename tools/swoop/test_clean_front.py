import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

# Strip parent transforms and apply
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow"] or o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

swoop_mesh = bpy.data.objects.get("Swoop.001")
pts = [v.co for v in swoop_mesh.data.vertices]
zs = [p.z for p in pts]
raw_h = max(zs) - min(zs)
print(f"Raw unparented Swoop height: {raw_h:.6f}m")

# Ramjet target height is 11.40m
scale_factor = 11.40 / raw_h
print(f"Required scale factor: {scale_factor:.4f}")

S_mat = Matrix.Scale(scale_factor, 4)
swoop_mesh.matrix_world = S_mat @ swoop_mesh.matrix_world
bpy.ops.object.select_all(action='DESELECT')
swoop_mesh.select_set(True)
bpy.context.view_layer.objects.active = swoop_mesh
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Grounding: lowest Z = 0.0
min_z = min(v.co.z for v in swoop_mesh.data.vertices)
for v in swoop_mesh.data.vertices:
    v.co.z -= min_z

new_zs = [v.co.z for v in swoop_mesh.data.vertices]
new_xs = [v.co.x for v in swoop_mesh.data.vertices]
new_ys = [v.co.y for v in swoop_mesh.data.vertices]
print(f"Swoop bounds after scaling & grounding:")
print(f"  X: [{min(new_xs):.3f}, {max(new_xs):.3f}] (span: {max(new_xs)-min(new_xs):.3f}m)")
print(f"  Y: [{min(new_ys):.3f}, {max(new_ys):.3f}] (span: {max(new_ys)-min(new_ys):.3f}m)")
print(f"  Z: [{min(new_zs):.3f}, {max(new_zs):.3f}] (span: {max(new_zs)-min(new_zs):.3f}m)")

# Check LeftHand and RightHand vertices
lh_vg = swoop_mesh.vertex_groups.get("Bone_L_Hand")
rh_vg = swoop_mesh.vertex_groups.get("Bone_R_Hand")
lh_pts = [v.co for v in swoop_mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.4 for g in v.groups)]
rh_pts = [v.co for v in swoop_mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.4 for g in v.groups)]
lh_c = sum(lh_pts, Vector((0,0,0))) / len(lh_pts)
rh_c = sum(rh_pts, Vector((0,0,0))) / len(rh_pts)
print(f"Left Hand center:  X={lh_c.x:+.3f}, Y={lh_c.y:+.3f}, Z={lh_c.z:+.3f}")
print(f"Right Hand center: X={rh_c.x:+.3f}, Y={rh_c.y:+.3f}, Z={rh_c.z:+.3f}")

# Assign master material with atlas diffuse texture
mat = bpy.data.materials.new("M_Swoop_Preview")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load("e:/Agent/TFTF-blender/3rd-party-models/swoop/02_textures/cha_swoop_main_Diffuse.png")
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
swoop_mesh.data.materials.clear()
swoop_mesh.data.materials.append(mat)

# Remap UVs to body tile [0.004, 0.746] x [0.254, 0.996]
uvl = swoop_mesh.data.uv_layers.active.data
for p in swoop_mesh.data.polygons:
    for li in p.loop_indices:
        u, v = uvl[li].uv
        cu = min(max(u, 0.004), 0.996)
        cv = min(max(v, 0.004), 0.996)
        uvl[li].uv = (0.004 + cu * (0.746 - 0.004), 0.254 + cv * (0.996 - 0.254))

# Setup camera centered at Z=5.7 looking at character
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0, -22, 5.7))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

# Lighting
light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 3.5
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

# Fill light
light2_data = bpy.data.lights.new("Sun2", type='SUN')
light2_data.energy = 1.5
light2 = bpy.data.objects.new("Sun2", light2_data)
bpy.context.scene.collection.objects.link(light2)
light2.rotation_euler = (0.785, -0.5, 3.14159)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_clean_front_preview.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_clean_front_preview.png")
