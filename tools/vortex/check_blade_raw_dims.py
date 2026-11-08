import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\weapons\vortex_weapons.blend")
blade_l = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]

# In raw blade mesh:
xs = [v.co.x for v in blade_l.data.vertices]
ys = [v.co.y for v in blade_l.data.vertices]
zs = [v.co.z for v in blade_l.data.vertices]
print(f"Raw Blade length along X: {max(xs) - min(xs):.3f}")
print(f"Raw Blade length along Y: {max(ys) - min(ys):.3f}")
print(f"Raw Blade length along Z: {max(zs) - min(zs):.3f}")
print(f"Raw bounds X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
