import bpy
import json
from mathutils import Vector, Matrix
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

gun = bpy.data.objects.get("StarSaberGun_R")
assert gun, "StarSaberGun_R not found in StarSaber.fbx!"

gun.parent = None
gun.matrix_world = Matrix.Identity(4)

# Scale by 4.0 to match Star Saber body & Motormaster rifle dimensions (length ~5.89m)
SCALE = 4.0
scale_mat = Matrix.Scale(SCALE, 4)
gun.data.transform(scale_mat)
gun.data.update()

# Calculate grip center
min_z = min(v.co.z for v in gun.data.vertices)
grip_verts = [v.co for v in gun.data.vertices if v.co.z < min_z + 0.2]
gun_grip_y = sum(v.y for v in grip_verts) / len(grip_verts)
gun_grip_z = min_z + 0.35  # center of hand wrap around handle

# In Motormaster, LeftHand palm grasp point is at (0.0, 0.4582, -1.20) in COG local space
# For a clean root bone COG at the hand grip, we translate so grip center is at (0, 0, 0) in gun local space,
# OR we align directly to Motormaster's exact local coordinate system:
# In Motormaster:
# gun Transform is at LeftHand: LocalPos=(-0.133, -0.720, 0.0), LocalRot=Identity
# child rifle Transform: LocalPos=(-1.045, 0.301, 1.474), LocalRot=Euler(0, 0, -90)
# And the mesh in COG space has grip at (0.0, 0.4582, -1.20)
target_grip = Vector((0.0, 0.4582, -1.20))
curr_grip = Vector((0.0, gun_grip_y, gun_grip_z))
trans = Matrix.Translation(target_grip - curr_grip)

gun.data.transform(trans)
gun.data.update()

# Remap UVs: U' = 0.5 + 0.5 * U, V' = V
uv_layer = gun.data.uv_layers.active.data
for loop in uv_layer:
    loop.uv[0] = 0.5 + 0.5 * loop.uv[0]
    # loop.uv[1] unchanged

gun.data.update()

# Triangulate
bpy.context.view_layer.objects.active = gun
gun.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')

mesh = gun.data
mesh.calc_normals_split()

verts = []
normals = []
uvs = []
triangles = []

# Unity coordinate conversion:
# Blender (X_right, Y_fwd, Z_up) -> Unity (X_right, Y_up, Z_fwd)
# In standard Blender-to-Unity: Unity.x = -Blender.x, Unity.y = Blender.z, Unity.z = -Blender.y
# But wait: let's verify if motormaster_rifle.obj was already exported in Unity or Blender space:
# motormaster_rifle.obj was exported by UnityPy directly from Unity mesh m_Vertices!
# UnityPy mesh.export() exports: v x y z directly from Unity m_Vertices!
# So motormaster_rifle.obj coordinates are in UNITY space!
# In motormaster_rifle.obj: X was [-0.47, 0.47], Y was [-4.33, 1.56] (length), Z was [-1.93, 0.97]!
# So in Unity space, Y is along the barrel, Z is vertical!
# In Blender space:
# If we export as Unity vectors:
# Let's inspect Unity axes!

out_data = {
    "verts": [[round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6)] for v in mesh.vertices],
    "uvs": [[round(mesh.uv_layers.active.data[li].uv[0], 6), round(mesh.uv_layers.active.data[li].uv[1], 6)] for li in range(len(mesh.uv_layers.active.data))],
    "polys": [[li for li in p.loop_indices] for p in mesh.polygons],
    "vertex_indices": [[v for v in p.vertices] for p in mesh.polygons]
}

out_path = Path(r"E:\Agent\TFTF-blender\scratch\starsaber_gun_geom.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out_data, f)

print(f"[✓] Exported {len(mesh.vertices)} verts, {len(mesh.polygons)} tris to {out_path}")
