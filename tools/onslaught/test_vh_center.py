import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

vh = bpy.data.objects.get("VH.dmx")
vh_arm = bpy.data.objects.get("Onslaught_VH_ARM")

print(f"Initial VH.dmx loc: {vh.location}, matrix_world: {vh.matrix_world.translation}")
print(f"Initial vh_arm loc: {vh_arm.location}, matrix_world: {vh_arm.matrix_world.translation}")

# Reset location
vh.location.x = 0
vh_arm.location.x = 0
vh.parent = vh_arm
mod = vh.modifiers.new(name="Onslaught_VH_ARM", type='ARMATURE')
mod.object = vh_arm

print(f"Centered VH.dmx loc: {vh.location}")
print(f"Centered vh_arm loc: {vh_arm.location}")
print("Modifiers on VH.dmx:", [m.name for m in vh.modifiers])
