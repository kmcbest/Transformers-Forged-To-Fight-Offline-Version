import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\StarSaber\source\StarSaber.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

sword = bpy.data.objects.get("StarSaberSword")
p = sword
chain = []
while p:
    chain.append((p.name, p.scale, p.rotation_euler, p.location))
    p = p.parent

print("Parent chain for StarSaberSword:")
for c in chain:
    print(f"  {c[0]}: loc={c[3]} rot={c[2]} scale={c[1]}")

local_verts = [v.co for v in sword.data.vertices]
print(f"Sword Local mesh coords: X=[{min(v.x for v in local_verts):.4f}, {max(v.x for v in local_verts):.4f}], Y=[{min(v.y for v in local_verts):.4f}, {max(v.y for v in local_verts):.4f}], Z=[{min(v.z for v in local_verts):.4f}, {max(v.z for v in local_verts):.4f}]")
