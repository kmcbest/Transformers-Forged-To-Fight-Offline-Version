import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

gl = bpy.data.objects.get("StarSaberGun_L")
gr = bpy.data.objects.get("StarSaberGun_R")

vl = [v.co for v in gl.data.vertices]
vr = [v.co for v in gr.data.vertices]

diff_same = max((a - b).length for a, b in zip(vl, vr))
diff_mirr_x = max((Vector((-a.x, a.y, a.z)) - b).length for a, b in zip(vl, vr))

print(f"Diff if identical: {diff_same:.6f}")
print(f"Diff if mirrored along X: {diff_mirr_x:.6f}")
