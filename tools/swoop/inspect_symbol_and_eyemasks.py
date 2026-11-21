import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_PATH = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
img = bpy.data.images.load(str(TEX_PATH))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)[::-1].copy()

# 1. Inspect Tx_Swoop_D_RGB in [640:755, 875:1005] to see what dark islands exist!
print("=== Dark pixels (maxRGB < 68, neutral) in Tx_Swoop_D_RGB [875:1005, 640:755] ===")
for py0 in range(640, 755, 5):
    row_info = []
    for px0 in range(875, 1005, 5):
        patch = tex[py0:py0+5, px0:px0+5]
        dk = (patch.max(axis=2) < 68) & ((patch.max(axis=2).astype(int) - patch.min(axis=2).astype(int)) < 18)
        if dk.sum() >= 5:
            row_info.append(f"{px0}..{px0+4}({dk.sum()})")
    if row_info:
        print(f"  py={py0:3d}..{py0+4:3d}: " + " ".join(row_info))

# 2. Check Vehicle Pteranodon Head polygons with max(rgb) < 68
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
vme = vh.data
vuvl = vme.uv_layers.active.data
print("\n=== Pteranodon Head polygons with dark texel (max<68, Z>2.2, Y<-0.5) ===")
eye_vh = []
for p in vme.polygons:
    if p.center.z > 2.2 and p.center.y < -0.5:
        us = [(vuvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
        vs = [(vuvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
        cu, cv = sum(us)/len(us), sum(vs)/len(vs)
        px = int(np.clip(cu, 0, 0.9999) * tw)
        py = int(np.clip(1.0 - cv, 0, 0.9999) * th)
        rgb = tex[py, px]
        if rgb.max() < 68 and (int(rgb.max()) - int(rgb.min())) < 18:
            eye_vh.append((p.center.x, p.center.y, p.center.z, px, py, tuple(int(c) for c in rgb), [((u[0]*tw), ((1-u[1])*th)) for u in zip(us, vs)]))

for label, flt in (("px<930", [e for e in eye_vh if e[3]<930]), ("px>=930", [e for e in eye_vh if e[3]>=930])):
    if flt:
        all_px = [pt[0] for e in flt for pt in e[6]]
        all_py = [pt[1] for e in flt for pt in e[6]]
        print(f"  {label}: polys={len(flt)} px=[{min(all_px):.1f},{max(all_px):.1f}] py=[{min(all_py):.1f},{max(all_py):.1f}] X=[{min(e[0] for e in flt):+.3f},{max(e[0] for e in flt):+.3f}] Y=[{min(e[1] for e in flt):.3f},{max(e[1] for e in flt):.3f}] Z=[{min(e[2] for e in flt):.3f},{max(e[2] for e in flt):.3f}] sample={flt[0][5]}")

# 3. Check Robot Chest Beak normal & surface where emblem should sit, plus Symbol_AB orientation relative to Swoop.001 in Posed Swoop_pbr.fbx!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")
arm = bpy.data.objects.get("Bip001")
deps = bpy.context.evaluated_depsgraph_get()
sym_ev = sym.evaluated_get(deps).data
sw_ev = sw.evaluated_get(deps).data
# Check posed Symbol_AB center & normal in Swoop world vs Robot Chest
# Also print bird_Head pose rotation/matrix in posed vs unposed
pb = arm.pose.bones.get("bird_Head")
if pb:
    print(f"\nPosed bird_Head matrix head={arm.matrix_world @ pb.head} tail={arm.matrix_world @ pb.tail}")
    print(f"Posed bird_Head rot_mode={pb.rotation_mode} rot_q={pb.rotation_quaternion} rot_e={pb.rotation_euler}")

# Check exact Mat[0] M_Symbol_AB vs Mat[1] M_Symbol_Black shapes in local space
s_me = sym.data
for mi, m in enumerate(s_me.materials):
    polys = [p for p in s_me.polygons if p.material_index == mi]
    ns = [p.normal for p in polys]
    avg_n = sum(ns, Vector((0,0,0))).normalized() if ns else Vector()
    print(f"  Symbol_AB Mat[{mi}] '{m.name}': polys={len(polys)}, local avg_n={avg_n}")

# Find where bird_Head is in build_aligned_swoop_robot's static pose!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
rme = rob.data
# Print beak front profile (X~0, Z in [6.0, 8.8]) with polygon normals!
beak_center = [p for p in rme.polygons if abs(p.center.x) < 0.15 and 6.5 <= p.center.z <= 8.5 and p.center.y < -0.5 and p.normal.y < -0.3]
beak_center.sort(key=lambda p: p.center.z)
print(f"\n=== Swoop Prepared Front Gold Beak center profile (polys={len(beak_center)}) ===")
for p in beak_center[::max(1, len(beak_center)//10)]:
    print(f"  Z={p.center.z:.3f} Y={p.center.y:.4f} normal=({p.normal.x:+.2f},{p.normal.y:+.2f},{p.normal.z:+.2f})")
