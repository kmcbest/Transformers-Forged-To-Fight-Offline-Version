import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import numpy as np
from pathlib import Path

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

for name in ["WEP_Hammer_SKEL.mo.dmx", "WEP_Hammer_SKEL.mo.001.dmx", "RB_Brawl_CHARSKEL_Chest.mo.dmx", "RB_Brawl_CHARSKEL_ArmLoR.mo.dmx", "VH_BrawlCINE_SKEL.001.dmx"]:
    o = bpy.data.objects.get(name)
    if o:
        xs = [(o.matrix_world @ v.co).x for v in o.data.vertices]
        ys = [(o.matrix_world @ v.co).y for v in o.data.vertices]
        zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
        print(f"{name:35s} X=[{min(xs):.2f},{max(xs):.2f}] Y=[{min(ys):.2f},{max(ys):.2f}] Z=[{min(zs):.2f},{max(zs):.2f}]")

# Also check BrawlTank bad UVs (which vertices have U > 5 or U < -5)
tank = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")
uvl = tank.data.uv_layers.active
t_mats = [s.material.name if s.material else "" for s in tank.material_slots]
bad_by_mat = {}
for poly in tank.data.polygons:
    mn = t_mats[poly.material_index] if poly.material_index < len(t_mats) else "?"
    us = [uvl.data[li].uv.x for li in poly.loop_indices]
    vs = [uvl.data[li].uv.y for li in poly.loop_indices]
    if max(us) > 2.0 or min(us) < -2.0 or max(vs) > 2.0 or min(vs) < -2.0:
        bad_by_mat[mn] = bad_by_mat.get(mn, 0) + 1
print("Tank out-of-range UV polygons by mat:", bad_by_mat)

# Check per-material UV min/max on all Brawl robot & tank meshes
print("\n=== PER-MATERIAL UV RANGES ===")
for name in [
    "RB_Brawl_CHARSKEL_Head.mo.dmx", "RB_Brawl_CHARSKEL_Chest.mo.dmx",
    "RB_Brawl_CHARSKEL_CapL.mo.dmx", "RB_Brawl_CHARSKEL_CapR.mo.dmx",
    "RB_Brawl_CHARSKEL_ArmLoL.mo.dmx", "RB_Brawl_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Brawl_CHARSKEL_Legs.mo.dmx", "BrawlCannon_STAT.mo.dmx", "BrawlCannon_STAT.mo.001.dmx",
    "VH_BrawlCINE_SKEL.001.dmx"
]:
    o = bpy.data.objects.get(name)
    uvl = o.data.uv_layers.active
    ms = [s.material.name if s.material else "" for s in o.material_slots]
    by_m = {}
    for poly in o.data.polygons:
        mn = ms[poly.material_index] if poly.material_index < len(ms) else "?"
        arr = by_m.setdefault(mn, [])
        for li in poly.loop_indices:
            arr.append((uvl.data[li].uv.x, uvl.data[li].uv.y))
    for mn, pts in by_m.items():
        a = np.array(pts)
        # Check percentile to see if 65504 is just a few junk verts
        print(f"  {name:32s} | {mn:30s}: n={len(a):5d} U=[{a[:,0].min():.3f}, {a[:,0].max():.3f}] p99=({np.percentile(a[:,0],1):.3f},{np.percentile(a[:,0],99):.3f}) V=[{a[:,1].min():.3f}, {a[:,1].max():.3f}] p99=({np.percentile(a[:,1],1):.3f},{np.percentile(a[:,1],99):.3f})")
