# -*- coding: utf-8 -*-
import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

head_verts = [v for v in mesh.data.vertices if any("Head" in mesh.vertex_groups[g.group].name or "Face" in mesh.vertex_groups[g.group].name for g in v.groups)]

# Set camera to focus on head
cam = bpy.data.objects.get("Camera") or bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
if cam.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Front-angle close up of head
cam.location = (0, -4.5, 9.3)
cam.rotation_euler = (math.radians(88.0), 0, 0)

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.color_type = 'MATERIAL'

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent

# Render 1: Original
bpy.context.scene.render.filepath = str(ROOT / "tools" / "demolishor" / "head_original.png")
bpy.ops.render.render(write_still=True)
print("[✓] Rendered original head")

# Lift head by +0.35m Z and +0.15m Y
for v in head_verts:
    v.co.z += 0.35
    v.co.y += 0.15
mesh.data.update()

# Render 2: Lifted
bpy.context.scene.render.filepath = str(ROOT / "tools" / "demolishor" / "head_lifted.png")
bpy.ops.render.render(write_still=True)
print("[✓] Rendered lifted head")
