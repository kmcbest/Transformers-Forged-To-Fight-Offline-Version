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
TEX_DIR = ROOT / "3rd-party-models/swoop/01_master/textures"
print("Texture files in 01_master/textures:", [p.name for p in TEX_DIR.iterdir()])

img = bpy.data.images.load(str(TEX_DIR / "Tx_Swoop_D_RGB.png"))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)[::-1].copy()

# Find any blue/cyan pixels in Tx_Swoop_D_RGB.png (b > r + 15 and b > 80) or bright eye pixels
r, g, b = tex[:,:,0].astype(int), tex[:,:,1].astype(int), tex[:,:,2].astype(int)
cyan_mask = (b > r + 20) & (b > 90) & (g > 70)
ys, xs = np.where(cyan_mask)
print(f"Blue/cyan pixels count={len(xs)}")
if len(xs) > 0:
    # cluster into boxes
    pts = list(zip(xs, ys))
    print(f"  overall cyan bbox: x=[{xs.min()},{xs.max()}], y=[{ys.min()},{ys.max()}]")

# Inspect Swoop_pbr.fbx UV layers and Symbol_AB + beak overlap
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")
arm = bpy.data.objects.get("Bip001")
print("\nSwoop.001 UV layers:", [u.name for u in sw.data.uv_layers])
print("Symbol_AB UV layers:", [u.name for u in sym.data.uv_layers])
print("Symbol_AB mats:", [m.name for m in sym.data.materials])
# Check Symbol_AB vertex groups
print("Symbol_AB vgs:", [vg.name for vg in sym.vertex_groups])

# Find where Symbol_AB sits when Armature is in Posed (frame 0) vs Rest (cleared) relative to Swoop.001 chest beak
deps = bpy.context.evaluated_depsgraph_get()
sym_ev = sym.evaluated_get(deps)
sw_ev = sw.evaluated_get(deps)
# Map both into world space
sym_w = [sym.matrix_world @ v.co for v in sym_ev.data.vertices]
sx0, sx1 = min(p.x for p in sym_w), max(p.x for p in sym_w)
sy0, sy1 = min(p.y for p in sym_w), max(p.y for p in sym_w)
sz0, sz1 = min(p.z for p in sym_w), max(p.z for p in sym_w)
sw_near = [sw.matrix_world @ v.co for v in sw_ev.data.vertices]
sw_in = [p for p in sw_near if sx0-0.002 <= p.x <= sx1+0.002 and sz0-0.002 <= p.z <= sz1+0.002]
print(f"Posed World Symbol_AB: X=[{sx0:.5f},{sx1:.5f}] Y=[{sy0:.5f},{sy1:.5f}] Z=[{sz0:.5f},{sz1:.5f}]")
if sw_in:
    print(f"Posed World Swoop.001 beak near Symbol: Y=[{min(p.y for p in sw_in):.5f},{max(p.y for p in sw_in):.5f}]")

# Inspect Robot Eyes in Unposed Swoop.001 by selecting front-facing Head faces around eye height
# Clear pose
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')
deps = bpy.context.evaluated_depsgraph_get()
sw_st = sw.evaluated_get(deps).data
sym_st = sym.evaluated_get(deps).data
sym_st_pts = [sym.matrix_world @ v.co for v in sym_st.vertices]
sw_st_pts = [sw.matrix_world @ v.co for v in sw_st.vertices]
print(f"Unposed World Symbol_AB: X=[{min(p.x for p in sym_st_pts):.5f},{max(p.x for p in sym_st_pts):.5f}] Y=[{min(p.y for p in sym_st_pts):.5f},{max(p.y for p in sym_st_pts):.5f}] Z=[{min(p.z for p in sym_st_pts):.5f},{max(p.z for p in sym_st_pts):.5f}]")
sx0, sx1 = min(p.x for p in sym_st_pts), max(p.x for p in sym_st_pts)
sz0, sz1 = min(p.z for p in sym_st_pts), max(p.z for p in sym_st_pts)
sw_st_in = [p for p in sw_st_pts if sx0-0.002 <= p.x <= sx1+0.002 and sz0-0.002 <= p.z <= sz1+0.002]
if sw_st_in:
    print(f"Unposed World Swoop.001 beak near Symbol: Y=[{min(p.y for p in sw_st_in):.5f},{max(p.y for p in sw_st_in):.5f}]")

# Also inspect ALL Robot Eye polygons (px ~ 890..930, py ~ 645..730 in Swoop.001) and print individual eye polygons!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data
print("\nswoop_prepared UV layers:", [u.name for u in me.uv_layers])
uvl = me.uv_layers.active.data
print("=== Robot Face Polygons around Z=[9.95, 10.35], Y < -0.30, |X| < 0.35 ===")
# Group by connected UV pixel coordinates
for p in me.polygons:
    if p.normal.y < -0.2 and p.center.y < -0.30 and 9.95 <= p.center.z <= 10.35 and abs(p.center.x) < 0.35:
        us = [(uvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
        vs = [(uvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
        cu, cv = sum(us)/len(us), sum(vs)/len(vs)
        px = int(np.clip(cu, 0, 0.9999) * tw)
        py = int(np.clip(1.0 - cv, 0, 0.9999) * th)
        rgb = tuple(int(c) for c in tex[py, px])
        # Check if inside dark eye socket (Z~10.12-10.30, |X|~0.05-0.27) or visor region
        if 885 <= px <= 945 and 645 <= py <= 725:
            print(f"  poly X={p.center.x:+.3f} Y={p.center.y:+.3f} Z={p.center.z:.3f} ny={p.normal.y:+.2f} px=({px:4d},{py:4d}) rgb={rgb}")
