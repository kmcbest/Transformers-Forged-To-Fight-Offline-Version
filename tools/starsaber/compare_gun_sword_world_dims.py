import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

gun = bpy.data.objects.get("StarSaberGun_R")
sword = bpy.data.objects.get("StarSaberSword")

gun_wverts = [gun.matrix_world @ v.co for v in gun.data.vertices]
sword_wverts = [sword.matrix_world @ v.co for v in sword.data.vertices]

def get_dims(verts):
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    return Vector((max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))

print(f"Gun world dimensions: {get_dims(gun_wverts)}")
print(f"Sword world dimensions: {get_dims(sword_wverts)}")
