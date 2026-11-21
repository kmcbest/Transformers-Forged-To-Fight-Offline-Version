import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix, Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_PATH = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
img = bpy.data.images.load(str(TEX_PATH))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)
# Flip vertically so row 0 is top (PIL convention)
tex = tex[::-1].copy()
print(f"Tx_Swoop_D_RGB.png: {tw}x{th}, mean lum={tex.mean():.1f}, max={tex.max()}, min={tex.min()}")

def sample_rgb(u, v):
    # u, v in source [0, 1] space
    px = int(np.clip(u, 0.0, 0.9999) * tw)
    py = int(np.clip(1.0 - v, 0.0, 0.9999) * th)
    return tuple(int(c) for c in tex[py, px]), px, py

# 1. Inspect Symbol_AB transform in Swoop_pbr.fbx vs Swoop.001
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")
arm = bpy.data.objects.get("Bip001")
print(f"\nSwoop.001 loc={sw.location} rot={sw.rotation_euler} scale={sw.scale} parent={sw.parent}")
print(f"Symbol_AB loc={sym.location} rot={sym.rotation_euler} scale={sym.scale} parent={sym.parent}")
if sym.modifiers:
    print("Symbol_AB modifiers:", [(m.name, m.type) for m in sym.modifiers])
for c in sym.constraints:
    print("Symbol_AB constraint:", c.type)

# Evaluate Symbol_AB with depsgraph in original posed Swoop_pbr.fbx vs unposed
deps = bpy.context.evaluated_depsgraph_get()
sym_eval = sym.evaluated_get(deps)
sw_eval = sw.evaluated_get(deps)
sym_w = [sym.matrix_world @ v.co for v in sym_eval.data.vertices]
sw_w = [sw.matrix_world @ v.co for v in sw_eval.data.vertices]
print(f"Evaluated Posed Symbol_AB world: X=[{min(p.x for p in sym_w):.5f},{max(p.x for p in sym_w):.5f}] Y=[{min(p.y for p in sym_w):.5f},{max(p.y for p in sym_w):.5f}] Z=[{min(p.z for p in sym_w):.5f},{max(p.z for p in sym_w):.5f}]")
print(f"Evaluated Posed Swoop.001 world: X=[{min(p.x for p in sw_w):.5f},{max(p.x for p in sw_w):.5f}] Y=[{min(p.y for p in sw_w):.5f},{max(p.y for p in sw_w):.5f}] Z=[{min(p.z for p in sw_w):.5f},{max(p.z for p in sw_w):.5f}]")

# Check unposed Bip001 (what build_aligned_swoop_robot.py did!)
rel_sym_mat = sw.matrix_world.inverted() @ sym.matrix_world
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')
deps = bpy.context.evaluated_depsgraph_get()
sw_static = sw.evaluated_get(deps).data
sym_rel_pts = [rel_sym_mat @ v.co for v in sym.data.vertices]
sw_static_pts = [v.co for v in sw_static.vertices]
print(f"Unposed Symbol_AB in Swoop.001 local: X=[{min(p.x for p in sym_rel_pts):.3f},{max(p.x for p in sym_rel_pts):.3f}] Y=[{min(p.y for p in sym_rel_pts):.3f},{max(p.y for p in sym_rel_pts):.3f}] Z=[{min(p.z for p in sym_rel_pts):.3f},{max(p.z for p in sym_rel_pts):.3f}]")
print(f"Unposed Swoop.001 local:              X=[{min(p.x for p in sw_static_pts):.3f},{max(p.x for p in sw_static_pts):.3f}] Y=[{min(p.y for p in sw_static_pts):.3f},{max(p.y for p in sw_static_pts):.3f}] Z=[{min(p.z for p in sw_static_pts):.3f},{max(p.z for p in sw_static_pts):.3f}]")

# 2. Check swoop_prepared.fbx (ALL verts & UVs of Symbol_AB if present, and Robot Eyes!)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data
uvl = me.uv_layers.active.data

u_gt_75 = [p for p in me.polygons if all(uvl[li].uv.x >= 0.75 for li in p.loop_indices)]
print(f"\nswoop_prepared polys with ALL uv.x >= 0.75: count={len(u_gt_75)}")
if u_gt_75:
    pts = [me.vertices[vi].co for p in u_gt_75 for vi in p.vertices]
    print(f"  X=[{min(p.x for p in pts):.3f},{max(p.x for p in pts):.3f}] Y=[{min(p.y for p in pts):.3f},{max(p.y for p in pts):.3f}] Z=[{min(p.z for p in pts):.3f},{max(p.z for p in pts):.3f}]")

# Sample Robot Head front-facing polygons (Y < -0.35, Z in [9.5, 10.6])
head_vg = rob.vertex_groups.get("Head")
hi = head_vg.index
front_head = [p for p in me.polygons if p.normal.y < -0.2 and p.center.y < -0.3 and 9.5 <= p.center.z <= 10.6 and any(g.group == hi and g.weight > 0.5 for g in me.vertices[p.vertices[0]].groups)]
print(f"\nRobot front head polys in Z=[9.5,10.6]: {len(front_head)}")
# Cluster by color & UV
eye_candidates = []
for p in front_head:
    us = [(uvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
    vs = [(uvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
    cu, cv = sum(us)/len(us), sum(vs)/len(vs)
    rgb, px, py = sample_rgb(cu, cv)
    # Check if around eye height Z=[9.95, 10.45] or colored (blue/cyan/yellow/dark/bright)
    if 9.95 <= p.center.z <= 10.45:
        eye_candidates.append((round(p.center.x, 3), round(p.center.y, 3), round(p.center.z, 3), round(cu, 4), round(cv, 4), px, py, rgb))

# Print unique (px//4, py//4) groups in eye_candidates
groups = {}
for item in eye_candidates:
    k = (item[5]//4, item[6]//4)
    groups.setdefault(k, []).append(item)
print("Robot head eye-height (Z=[9.95,10.45]) UV groups:")
for k, items in sorted(groups.items()):
    xs = [i[0] for i in items]; ys = [i[1] for i in items]; zs = [i[2] for i in items]
    pxs = [i[5] for i in items]; pys = [i[6] for i in items]
    rgbs = [i[7] for i in items]
    mean_rgb = tuple(int(sum(c[j] for c in rgbs)/len(rgbs)) for j in range(3))
    print(f"  polys={len(items):3d} px=[{min(pxs)},{max(pxs)}] py=[{min(pys)},{max(pys)}] X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}] meanRGB={mean_rgb}")

# 3. Check Vehicle FBX Pteranodon Head polygons (find nose/beak tip front-most polygons!)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
vme = vh.data
vuvl = vme.uv_layers.active.data
# Look for front head/beak/eye area in swoop_vh_prepared.fbx (min Y / max X / etc. print overall bbox & chop1_chest_center/chop1_back_center)
vpts = [v.co for v in vme.vertices]
print(f"\nVehicle bbox: X=[{min(p.x for p in vpts):.2f},{max(p.x for p in vpts):.2f}] Y=[{min(p.y for p in vpts):.2f},{max(p.y for p in vpts):.2f}] Z=[{min(p.z for p in vpts):.2f},{max(p.z for p in vpts):.2f}]")
for vg_name in ("chop1_chest_center", "chop1_back_center", "chop1_head_center", "chop1_chest_hidden_center"):
    vg = vh.vertex_groups.get(vg_name)
    if vg:
        gpts = [v.co for v in vme.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
        if gpts:
            print(f"  VG {vg_name}: verts={len(gpts)} X=[{min(p.x for p in gpts):.2f},{max(p.x for p in gpts):.2f}] Y=[{min(p.y for p in gpts):.2f},{max(p.y for p in gpts):.2f}] Z=[{min(p.z for p in gpts):.2f},{max(p.z for p in gpts):.2f}]")

# Sample Pteranodon forward head polys (check nose axis: front of bird!)
# Find forward direction by seeing which end has wings vs beak (nose cone!)
# Let's bin ALL head-like polys near center X=[-0.7, 0.7] and high Z > 2.2
vh_head_polys = [p for p in vme.polygons if abs(p.center.x) < 0.7 and p.center.z > 2.0]
vgroups = {}
for p in vh_head_polys:
    us = [(vuvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
    vs = [(vuvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
    cu, cv = sum(us)/len(us), sum(vs)/len(vs)
    rgb, px, py = sample_rgb(cu, cv)
    k = (px // 16, py // 16)
    vgroups.setdefault(k, []).append((p.center.x, p.center.y, p.center.z, px, py, rgb))

print("Vehicle central-high polys (|X|<0.7, Z>2.0) UV clusters (px//16, py//16):")
for k, items in sorted(vgroups.items(), key=lambda kv: -len(kv[1])):
    if len(items) < 4:
        continue
    xs = [i[0] for i in items]; ys = [i[1] for i in items]; zs = [i[2] for i in items]
    pxs = [i[3] for i in items]; pys = [i[4] for i in items]
    rgbs = [i[5] for i in items]
    mean_rgb = tuple(int(sum(c[j] for c in rgbs)/len(rgbs)) for j in range(3))
    print(f"  polys={len(items):4d} px=[{min(pxs):4d},{max(pxs):4d}] py=[{min(pys):4d},{max(pys):4d}] X=[{min(xs):.2f},{max(xs):.2f}] Y=[{min(ys):.2f},{max(ys):.2f}] Z=[{min(zs):.2f},{max(zs):.2f}] meanRGB={mean_rgb}")
