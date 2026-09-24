# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

print("Mesh parent:", mesh.parent)
print("Mesh matrix_local:\n", mesh.matrix_local)
print("Mesh matrix_world:\n", mesh.matrix_world)
print("Armature matrix_world:\n", arm.matrix_world)
