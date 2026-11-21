import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

wpn = bpy.data.objects.get("Swoop_Weapon")
if wpn:
    print(f"parent: {wpn.parent.name if wpn.parent else None}")
    print(f"parent_type: {wpn.parent_type}")
    print(f"parent_bone: {wpn.parent_bone}")
    print(f"modifiers: {[m.type for m in wpn.modifiers]}")
    for m in wpn.modifiers:
        if m.type == 'ARMATURE':
            print(f"  Armature modifier object: {m.object.name}")
