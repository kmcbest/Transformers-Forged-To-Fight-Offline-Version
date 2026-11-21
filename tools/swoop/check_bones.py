import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
wpn = bpy.data.objects.get("Swoop_Weapon")

# Check rest pose bone matrices
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
rh_eb = arm.data.edit_bones.get("Bone_R_Hand")
bp_eb = arm.data.edit_bones.get("Bone_Pistol")
print(f"Edit Bone_R_Hand head: {rh_eb.head}")
print(f"Edit Bone_Pistol head: {bp_eb.head}")
print(f"Edit Bone_Pistol parent: {bp_eb.parent.name}")

# Now in object mode, check where Swoop_Weapon vertices are relative to Bone_Pistol
bpy.ops.object.mode_set(mode='OBJECT')
pts = [wpn.matrix_world @ v.co for v in wpn.data.vertices]
print(f"Swoop_Weapon world mean pos: {sum(pts, bpy.mathutils.Vector((0,0,0))) / len(pts)}")
print(f"Armature world pos: {arm.matrix_world.to_translation()}")
