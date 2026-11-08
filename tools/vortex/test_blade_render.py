import bpy
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

blade_l = bpy.data.objects.get("WEP_IonBlade_SKEL.mo_L.dmx")
tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures"

# delete everything except blade_l
for obj in list(bpy.data.objects):
    if obj != blade_l:
        bpy.data.objects.remove(obj, do_unlink=True)

# setup materials
for mat_slot in blade_l.material_slots:
    mat = mat_slot.material
    if not mat: continue
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    out = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    tex_node = nodes.new(type='ShaderNodeTexImage')
    
    if "bladeaut" in mat.name.lower():
        tex_path = os.path.join(tex_dir, "wep_bladeaut_mat.jpg")
    else:
        tex_path = os.path.join(tex_dir, "wep.jpg")
        
    if os.path.exists(tex_path):
        img = bpy.data.images.load(tex_path)
        tex_node.image = img
        mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

# Center camera on blade
bpy.ops.object.camera_add(location=(0, -4, 2), rotation=(1.3, 0, 0))
cam = bpy.context.object
bpy.context.scene.camera = cam

# Light
bpy.ops.object.light_add(type='SUN', location=(2, -2, 5))

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 600
out_png = r"E:\Agent\TFTF-blender\tools\vortex\blade_preview.png"
bpy.context.scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print(f"Rendered blade preview to: {out_png}")
