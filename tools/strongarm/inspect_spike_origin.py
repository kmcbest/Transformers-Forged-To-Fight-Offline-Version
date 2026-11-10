import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

# Check vertices inside Raw Strongarm.fbx on ALL Left arm meshes in Z_blender 4.2..5.0 region
# Specifically inspect bot:arm_geo_L vs bot:palm_geo_L vs bot:topLight_geo_L!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')

# Print bounding box of vertices weighted to EACH bone near wrist/forearm (X>1.5, 4.1<Z<5.1)
for bn in ["LeftArm", "LeftForeArm", "LeftHand", "LeftHandThumb1", "LeftHandThumb2", "LeftHandIndex1", "LeftHandPinky1"]:
    vg = mesh.vertex_groups.get(bn)
    if not vg:
        continue
    pts = [v.co for v in mesh.data.vertices if v.co.x > 1.5 and any(g.group == vg.index and g.weight > 0.05 for g in v.groups)]
    # check any vertices above Z=4.35 with Hand or Finger weight!
    high = [v.co for v in mesh.data.vertices if v.co.x > 1.5 and v.co.z > 4.35 and any(g.group == vg.index and g.weight > 0.05 for g in v.groups)]
    if high:
        print(f"{bn:16s} vertices > Z=4.35: count={len(high):3d} maxZ={max(p.z for p in high):.3f} X=[{min(p.x for p in high):.3f},{max(p.x for p in high):.3f}] Y=[{min(p.y for p in high):.3f},{max(p.y for p in high):.3f}]")

# Test in Blender Pose Mode: rotate LeftHand around X/Y/Z AND check if ANY triangle splits or protrudes outside forearm cuff!
# Better: check mesh polygons whose vertices have MIXED weights between LeftForeArm and LeftHand/Thumb1!
mixed_polys = []
for poly in mesh.data.polygons:
    bsets = set()
    zs = []
    xs = []
    for vi in poly.vertices:
        v = mesh.data.vertices[vi]
        if v.co.x > 1.7 and 4.1 < v.co.z < 5.0:
            xs.append(v.co.x)
            zs.append(v.co.z)
            for g in v.groups:
                if g.weight > 0.05:
                    bsets.add(mesh.vertex_groups[g.group].name)
    if zs and len(bsets) > 1 and ("LeftForeArm" in bsets):
        mixed_polys.append((min(zs), max(zs), max(xs), sorted(bsets)))
print(f"\nPolygons mixing LeftForeArm + other bones in wrist zone: {len(mixed_polys)}")
for mp in mixed_polys[:20]:
    print(" ", mp)
