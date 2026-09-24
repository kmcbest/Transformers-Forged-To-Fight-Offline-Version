# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

print("Checking weapon bones in Armature:")
for b in arm.data.bones:
    if "wpn" in b.name.lower() or "gun" in b.name.lower() or "cannon" in b.name.lower():
        print(" ", b.name)

print("\nChecking vertex groups containing weapon/cannon:")
for vg in mesh.vertex_groups:
    if "wpn" in vg.name.lower() or "gun" in vg.name.lower() or "cannon" in vg.name.lower():
        print(" ", vg.name)
