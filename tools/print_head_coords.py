import bpy
import bmesh

bpy.ops.wm.read_factory_settings(use_empty=True)
obj_path = r"E:\Agent\TFTF-blender\tools\bumblebee_cin\cha_bumblebee_cin_dotm_00.obj"
bpy.ops.wm.obj_import(filepath=obj_path)

obj = bpy.context.scene.objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)

print(f"Total faces: {len(bm.faces)}")
# Find top 20 faces by Z (highest up)
sorted_faces = sorted(bm.faces, key=lambda f: f.calc_center_bounds().z, reverse=True)
print("Top 15 faces with highest Z:")
for f in sorted_faces[:15]:
    c = f.calc_center_bounds()
    print(f"  Z={c.z:.3f}, Y={c.y:.3f}, X={c.x:.3f}, normal=({f.normal.x:.2f}, {f.normal.y:.2f}, {f.normal.z:.2f})")

# Also let's inspect faces around Z in [8.8, 9.4] with abs(X) < 0.5
print("\nSample faces in Z [8.9, 9.2], abs(X) < 0.5:")
count = 0
for f in bm.faces:
    c = f.calc_center_bounds()
    if 8.9 <= c.z <= 9.2 and abs(c.x) < 0.5:
        print(f"  Z={c.z:.3f}, Y={c.y:.3f}, X={c.x:.3f}, normal=({f.normal.x:.2f}, {f.normal.y:.2f}, {f.normal.z:.2f})")
        count += 1
        if count >= 20:
            break
print(f"Found at least {count} faces matching.")
