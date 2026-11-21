import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix
import math
from pathlib import Path
import shutil

print("=== [StarSaber] Building Centered & Oriented Gun FBX ===")

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

gun = bpy.data.objects.get("StarSaberGun_R")
assert gun, "StarSaberGun_R not found in StarSaber.fbx!"

gun.name = "cha_starsaber_gun"
gun.parent = None
gun.matrix_world = Matrix.Identity(4)

for o in list(bpy.data.objects):
    if o != gun:
        bpy.data.objects.remove(o, do_unlink=True)

# 1. Uniform scaling by 4.0
SCALE = 4.0
gun.data.transform(Matrix.Scale(SCALE, 4))
gun.data.update()

# 2. Rotate around X by -90 deg: barrel (-Y) -> +Z, top rail (+Z) -> +Y, grip (-Z) -> -Y
rot_x = Matrix.Rotation(math.radians(-90.0), 4, 'X')
gun.data.transform(rot_x)
gun.data.update()

# 3. Center grip at (0, 0, 0)
verts = [v.co for v in gun.data.vertices]
ys = [v.y for v in verts]
min_y = min(ys)
handle_verts = [v for v in verts if v.y < min_y + 0.6]
handle_center = Vector((
    sum(v.x for v in handle_verts) / len(handle_verts),
    sum(v.y for v in handle_verts) / len(handle_verts),
    sum(v.z for v in handle_verts) / len(handle_verts)
))
print(f"Grip Center before translation: {handle_center}")

gun.data.transform(Matrix.Translation(-handle_center))
gun.data.update()

# 4. Remap UVs: U' = 0.5 + 0.5 * U
uv_layer = gun.data.uv_layers.active.data
for loop in uv_layer:
    loop.uv[0] = 0.5 + 0.5 * loop.uv[0]
gun.data.update()

# 5. Create 1-bone Armature for COG
arm_data = bpy.data.armatures.new(name="GunArmature")
arm_obj = bpy.data.objects.new(name="cha_starsaber_gun_rig", object_data=arm_data)
bpy.context.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.object.mode_set(mode='EDIT')
bone = arm_data.edit_bones.new(name="COG")
bone.head = Vector((0.0, 0.0, 0.0))
bone.tail = Vector((0.0, 0.0, 1.0))
bpy.ops.object.mode_set(mode='OBJECT')

gun.vertex_groups.clear()
vg = gun.vertex_groups.new(name="COG")
vg.add(list(range(len(gun.data.vertices))), 1.0, 'REPLACE')

mod = gun.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
gun.parent = arm_obj

gun.data.materials.clear()
mat = bpy.data.materials.new(name="cha_starsaber_wpns")
gun.data.materials.append(mat)

OUT_FBX = Path(r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\03_fbx_exports\starsaber_gun_prepared.fbx")
OUT_FBX.parent.mkdir(parents=True, exist_ok=True)
UNITY_FBX = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\StarSaber\starsaber_gun_prepared.fbx")

gun.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

# Export with standard -Z forward, Y up
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    add_leaf_bones=False,
    bake_anim=False,
    axis_forward='-Z',
    axis_up='Y'
)
print(f"[✓] Exported FBX to {OUT_FBX} ({OUT_FBX.stat().st_size} bytes)")

shutil.copy2(OUT_FBX, UNITY_FBX)
print(f"[✓] Copied FBX to Unity: {UNITY_FBX}")
