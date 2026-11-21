import bpy
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Motormaster reference rifle
bpy.ops.import_scene.obj(filepath=r"E:\Agent\TFTF-blender\scratch\motormaster_rifle.obj")
mm_gun = bpy.context.selected_objects[0]
mm_gun.name = "Ref_MM_Gun"

# 2. Import StarSaber FBX
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

gun = bpy.data.objects.get("StarSaberGun_R")
gun.parent = None
gun.matrix_world = Matrix.Identity(4)

# Keep only mm_gun and gun
for o in list(bpy.data.objects):
    if o not in (mm_gun, gun):
        bpy.data.objects.remove(o, do_unlink=True)

SCALE = 4.0
scale_mat = Matrix.Scale(SCALE, 4)
gun.data.transform(scale_mat)
gun.data.update()

gun_verts = gun.data.vertices
min_z = min(v.co.z for v in gun_verts)
grip_verts = [v.co for v in gun_verts if v.co.z < min_z + 0.2]
gun_grip_y = sum(v.y for v in grip_verts) / len(grip_verts)
gun_grip_z = min_z + 0.35

target_grip = Vector((0.0, 0.4582, -1.20))
curr_grip = Vector((0.0, gun_grip_y, gun_grip_z))
trans = Matrix.Translation(target_grip - curr_grip)

gun.data.transform(trans)
gun.data.update()

print("StarSaber Gun aligned:")
xs = [v.co.x for v in gun.data.vertices]
ys = [v.co.y for v in gun.data.vertices]
zs = [v.co.z for v in gun.data.vertices]
print(f"  X: [{min(xs):.4f}, {max(xs):.4f}] (size {max(xs)-min(xs):.4f})")
print(f"  Y: [{min(ys):.4f}, {max(ys):.4f}] (size {max(ys)-min(ys):.4f})")
print(f"  Z: [{min(zs):.4f}, {max(zs):.4f}] (size {max(zs)-min(zs):.4f})")
