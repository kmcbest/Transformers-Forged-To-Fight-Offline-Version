import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Onslaught_ARM")

# Reset RocketLaunchers
for rname in ["RB_RocketLauncherL_SKEL.mo.dmx", "RB_RocketLauncherR_SKEL.mo.dmx"]:
    rl = bpy.data.objects.get(rname)
    rl.location = (0, 0, 0)
    rl.parent = arm
    mod = rl.modifiers.new(name="Onslaught_ARM", type='ARMATURE')
    mod.object = arm

print("Successfully attached and reset RocketLaunchers to Onslaught_ARM!")
