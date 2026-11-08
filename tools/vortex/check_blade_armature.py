import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\weapons\vortex_weapons.blend")
blade_l = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]
arm_l = bpy.data.objects.get("WEP_IonBlade_SKEL_L")

xs = [v.co.x for v in blade_l.data.vertices]
ys = [v.co.y for v in blade_l.data.vertices]
zs = [v.co.z for v in blade_l.data.vertices]
print(f"Blade_L bounds: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
if arm_l and arm_l.type == 'ARMATURE':
    print(f"Bones in blade armature ({len(arm_l.data.bones)}): {[b.name for b in arm_l.data.bones]}")
