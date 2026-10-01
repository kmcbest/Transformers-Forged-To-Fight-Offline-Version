import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

ghost = bpy.data.objects.get("Ironhide_Ghost_Reference")
if ghost:
    verts = [ghost.matrix_world @ v.co for v in ghost.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    print(f"Ironhide Ghost AABB:")
    print(f"  X: {min(xs):.2f} to {max(xs):.2f}")
    print(f"  Y: {min(ys):.2f} to {max(ys):.2f}")
    print(f"  Z: {min(zs):.2f} to {max(zs):.2f}")

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
if mesh:
    verts = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    zs = [v.z for v in verts]
    print(f"Demolishor Mesh AABB:")
    print(f"  X: {min(xs):.2f} to {max(xs):.2f}")
    print(f"  Y: {min(ys):.2f} to {max(ys):.2f}")
    print(f"  Z: {min(zs):.2f} to {max(zs):.2f}")
