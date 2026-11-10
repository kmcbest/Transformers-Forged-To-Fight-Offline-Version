import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
import math
import mathutils
from pathlib import Path

# 1. Inspect Raw Strongarm.fbx parts AFTER armature apply + Maya->Blender coords
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if orig_arm.animation_data:
    orig_arm.animation_data_clear()
orig_arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

print("=== Strongarm.fbx Left Arm & Torso Parts (Raw Maya Coords after Armature Apply) ===")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH':
        continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        if m.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=m.name)
    o.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if ("_l" in o.name.lower() or "waist" in o.name.lower() or "upperleg_geo_l" in o.name.lower() or "leg_geo_l" in o.name.lower()):
        vs = [v.co for v in o.data.vertices]
        xs = [v.x for v in vs]; ys = [v.y for v in vs]; zs = [v.z for v in vs]
        cx, cy, cz = sum(xs)/len(vs), sum(ys)/len(vs), sum(zs)/len(vs)
        if any(k in o.name.lower() for k in ("arm", "elbow", "shoulder", "hand", "palm", "fender", "light", "waist", "leg_geo_l", "upperleg_geo_l", "knee_geo_l")):
            print(f"  {o.name:28s} center=({cx:+.4f}, {cy:+.4f}, {cz:+.4f}) X=[{min(xs):+.4f},{max(xs):+.4f}] Y=[{min(ys):+.4f},{max(ys):+.4f}]")

# Check weighted centroid of each finger vertex group in bot:palm_geo_L
palm = bpy.data.objects.get("bot:palm_geo_L")
if palm:
    print("\n=== bot:palm_geo_L Finger VG Weighted Centroids (Raw Maya Coords) ===")
    for vg in palm.vertex_groups:
        wsum = 0.0
        csum = mathutils.Vector((0, 0, 0))
        for v in palm.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.1:
                    csum += v.co * g.weight
                    wsum += g.weight
        if wsum > 0:
            c = csum / wsum
            print(f"  {vg.name:20s}: wsum={wsum:6.1f} center=({c.x:+.4f}, {c.y:+.4f}, {c.z:+.4f})")

# 2. Check current strongarm_prepared.fbx (in Blender space) arm/hand/knee positions
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
arm_sa = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh_sa = next(o for o in bpy.data.objects if o.type == 'MESH')
print("\n=== Current strongarm_prepared.fbx (Blender Z-up) Left Arm & Leg VG Centers ===")
for vgn in ["LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "LeftUpLeg", "LeftLeg"]:
    vg = mesh_sa.vertex_groups.get(vgn)
    if not vg:
        continue
    pts = [v.co for v in mesh_sa.data.vertices if any(g.group == vg.index and g.weight > 0.1 for g in v.groups)]
    if pts:
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        print(f"  {vgn:14s} (verts={len(pts):4d}): center=({sum(xs)/len(pts):+.3f},{sum(ys)/len(pts):+.3f},{sum(zs)/len(pts):+.3f}) X=[{min(xs):+.3f},{max(xs):+.3f}] Z=[{min(zs):+.3f},{max(zs):+.3f}]")
