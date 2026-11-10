import bpy
import math

SCRATCH = r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_vh_prepared.fbx")

vh = [o for o in bpy.data.objects if o.type == 'MESH'][0]

# Assign calibrated strongarm_vh_a.png texture
mat = bpy.data.materials.new("PreviewMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
bsdf = nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value = 0.45
bsdf.inputs["Metallic"].default_value = 0.05
tex = nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\cha_strongarm_vh_a.png")
links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
vh.data.materials.clear()
vh.data.materials.append(mat)

# Lighting
scene = bpy.context.scene
scene.render.engine = 'CYCLES' if 'CYCLES' in dir(bpy.types) else 'BLENDER_EEVEE'
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 32
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.14, 0.16, 0.20, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.2

def add_sun(name, rot_deg, energy):
    ld = bpy.data.lights.new(name, type='SUN')
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    lo.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    scene.collection.objects.link(lo)

add_sun("Key", (50, 15, -135), 3.0)
add_sun("Fill", (65, 0, 45), 1.5)

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam

def point_at(pos, target=(0, 0, 1.2)):
    from mathutils import Vector
    cam.location = Vector(pos)
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

# Side View (+X looking toward 0 -> front -Y is left, rear +Y is right)
point_at((9.5, 0.0, 1.45), (0.0, 0.0, 1.35))
scene.render.filepath = SCRATCH + r"\blender_vh_fixed_side.png"
bpy.ops.render.render(write_still=True)

# Front 3/4 View (from -Y / +X looking toward hood, grille, roof lightbar)
point_at((5.2, -7.2, 3.1), (0.0, -0.3, 1.2))
scene.render.filepath = SCRATCH + r"\blender_vh_fixed_34.png"
bpy.ops.render.render(write_still=True)
print("Rendered Blender verification views!")
