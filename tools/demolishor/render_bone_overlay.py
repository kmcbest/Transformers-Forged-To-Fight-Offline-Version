# -*- coding: utf-8 -*-
import bpy
import math
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")

bpy.context.scene.frame_set(0)

# Make sure armature is selected, visible, in front
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
if arm:
    arm.hide_viewport = False
    arm.hide_render = False
    arm.show_in_front = True
    arm.data.display_type = 'OCTAHEDRAL'

cam = bpy.data.objects.get("Camera")
if not cam:
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

cam.location = (0, -10.0, 4.3)
cam.rotation_euler = (math.radians(90.0), 0, 0)

# Let's set shading
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'SOLID'
                space.overlay.show_bones = True
                space.overlay.show_wireframes = True

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
out_path = str(ROOT / "tools" / "demolishor" / "preview_perfect_stance_bones.png")
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1350
bpy.context.scene.render.filepath = out_path

# To make armature visible in standard render, we can convert bone pose to temporary display mesh or use opengl render
# Let's create visual bone meshes along bone head-tail segments so they show in Workbench render!
bone_mesh_data = bpy.data.meshes.new("Bone_Visuals")
bm_obj = bpy.data.objects.new("Bone_Visuals", bone_mesh_data)
bpy.context.scene.collection.objects.link(bm_obj)

verts = []
edges = []
key_bones = ["LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot",
             "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"]

# Also add finger bone lines
fingers = [b for b in arm.pose.bones if "finger" in b.name.lower() or "thumb" in b.name.lower() or "hand" in b.name.lower()]
key_bones = list(set(key_bones + [b.name for b in fingers]))

idx = 0
for bname in key_bones:
    b = arm.pose.bones.get(bname)
    if b:
        h = arm.matrix_world @ b.head
        t = arm.matrix_world @ b.tail
        # Create a small cross/diamond at joint head
        r = 0.08
        verts.extend([
            h,
            t,
            h + mathutils.Vector((r, 0, 0)),
            h - mathutils.Vector((r, 0, 0)),
            h + mathutils.Vector((0, 0, r)),
            h - mathutils.Vector((0, 0, r))
        ])
        edges.extend([
            (idx, idx+1),
            (idx+2, idx+3),
            (idx+4, idx+5)
        ])
        idx += 6

import mathutils
bone_mesh_data.from_pydata(verts, edges, [])
bone_mesh_data.update()

# Add skin modifier to make bones thick cylinders
mod = bm_obj.modifiers.new(name="Skin", type='SKIN')
# Give bright red/yellow emission material
mat = bpy.data.materials.new(name="BoneMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()
emit = nodes.new(type='ShaderNodeEmission')
emit.inputs['Color'].default_value = (1.0, 0.2, 0.0, 1.0) # Bright orange/red
emit.inputs['Strength'].default_value = 5.0
out = nodes.new(type='ShaderNodeOutputMaterial')
mat.node_tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
bm_obj.data.materials.append(mat)

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered overlay preview to {out_path}")
