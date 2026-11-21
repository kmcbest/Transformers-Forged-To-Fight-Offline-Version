import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_PATH = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
img = bpy.data.images.load(str(TEX_PATH))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)[::-1].copy()

def uv_px(u, v):
    return ((u - 0.004) / (0.746 - 0.004)) * tw, (1.0 - (v - 0.254) / (0.996 - 0.254)) * th

# 1. Inspect Robot Missile Length & ALL Face Polygons around Eyes (Z in [9.85, 10.32], |X| < 0.30, Y < -0.35)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
rme = rob.data
ruvl = rme.uv_layers["UV0"].data

# Find Robot wing missile pods (wing cannons at |X| > 2.8, behind shoulders Y > 0.2)
rob_missile_zs = [v.co.z for v in rme.vertices if abs(v.co.x) > 3.2 and v.co.y > 0.0]
if rob_missile_zs:
    print(f"Robot Wing Missile Z span: [{min(rob_missile_zs):.3f}, {max(rob_missile_zs):.3f}] -> length = {max(rob_missile_zs)-min(rob_missile_zs):.3f}m")
# Better: check outer wing pod vertices (say |X| in [3.3, 4.3] — let's check X/Y/Z ranges of wing pods)
for xlo, xhi in ((3.0, 3.8), (3.6, 4.3), (2.8, 3.6)):
    pts = [v.co for v in rme.vertices if xlo <= abs(v.co.x) <= xhi and v.co.z > 4.0]
    if pts:
        print(f"  Robot wing |X| in [{xlo},{xhi}]: n={len(pts)} Z=[{min(p.z for p in pts):.3f},{max(p.z for p in pts):.3f}] lenZ={max(p.z for p in pts)-min(p.z for p in pts):.3f}m")

print("\n=== ALL Robot Front Face Polygons sorted by Z (Z in [9.95, 10.33], |X| < 0.28, Y < -0.38, ny < -0.2) ===")
face_polys = []
for p in rme.polygons:
    if 9.95 <= p.center.z <= 10.33 and abs(p.center.x) < 0.28 and p.center.y < -0.38 and p.normal.y < -0.2:
        pts = [uv_px(ruvl[li].uv.x, ruvl[li].uv.y) for li in p.loop_indices]
        cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
        rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
        xs_uv = [pt[0] for pt in pts]; ys_uv = [pt[1] for pt in pts]
        face_polys.append((p.center.z, p.center.x, p.center.y, p.normal.z, cx, cy, min(xs_uv), max(xs_uv), min(ys_uv), max(ys_uv), rgb))

face_polys.sort(key=lambda t: -t[0])
for f in face_polys:
    print(f"  Z={f[0]:.3f} X={f[1]:+.3f} Y={f[2]:+.3f} nz={f[3]:+.2f} | uv_px=({f[4]:5.1f},{f[5]:5.1f}) box=[{f[6]:.1f}..{f[7]:.1f}, {f[8]:.1f}..{f[9]:.1f}] rgb={f[10]}")

# Also check if there are recessed/tilted eye-socket polygons in Head (ny <= 0.1 and |X| in [0.04, 0.25], Z in [10.02, 10.22], Y < -0.35)
print("\n=== Recessed / Slanted Eye Polygons (Z in [10.02, 10.22], |X| in [0.03,0.26], Y < -0.35, ANY normal) ===")
for p in rme.polygons:
    if 10.02 <= p.center.z <= 10.22 and 0.03 <= abs(p.center.x) <= 0.26 and p.center.y < -0.35:
        pts = [uv_px(ruvl[li].uv.x, ruvl[li].uv.y) for li in p.loop_indices]
        cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
        rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
        # print if dark or recessed or downward/upward normal
        if max(rgb) < 110 or abs(p.normal.y) < 0.5:
            xs_uv = [pt[0] for pt in pts]; ys_uv = [pt[1] for pt in pts]
            print(f"  Z={p.center.z:.3f} X={p.center.x:+.3f} Y={p.center.y:+.3f} n=({p.normal.x:+.2f},{p.normal.y:+.2f},{p.normal.z:+.2f}) uv=({cx:5.1f},{cy:5.1f}) box=[{min(xs_uv):.1f}..{max(xs_uv):.1f},{min(ys_uv):.1f}..{max(ys_uv):.1f}] rgb={rgb}")

# 2. Inspect Vehicle Missile Pod Length & Pteranodon Beak Mouth Coords
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
vme = vh.data
for vg_name in ("chop1_cannon_left", "chop1_cannon_right", "chop1_forearm_left"):
    vg = vh.vertex_groups.get(vg_name)
    if vg:
        pts = [v.co for v in vme.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
        if pts:
            print(f"\nVehicle VG {vg_name}: Y=[{min(p.y for p in pts):.3f},{max(p.y for p in pts):.3f}] lenY={max(p.y for p in pts)-min(p.y for p in pts):.3f}m, X=[{min(p.x for p in pts):.2f},{max(p.x for p in pts):.2f}]")
# Also check forward-pointing cylindrical missile pod on Vehicle (|X| in [2.3, 3.2], Z < 2.2)
vh_pod = [v.co for v in vme.vertices if 2.3 <= abs(v.co.x) <= 3.2 and v.co.z < 2.3]
if vh_pod:
    print(f"Vehicle Missile Pod (|X| in [2.3,3.2], Z<2.3): Y=[{min(p.y for p in vh_pod):.3f},{max(p.y for p in vh_pod):.3f}] lenY={max(p.y for p in vh_pod)-min(p.y for p in vh_pod):.3f}m")
# Find Pteranodon beak mouth position in cha_swoop_vh local space
beak_pts = [v.co for v in vme.vertices if abs(v.co.x) < 0.25 and v.co.y < -1.5]
if beak_pts:
    print(f"Vehicle Beak Tip area (Y < -1.5): minY={min(p.y for p in beak_pts):.3f}, Z=[{min(p.z for p in beak_pts):.3f},{max(p.z for p in beak_pts):.3f}]")
# Find mouth opening (gap between upper beak and lower jaw around Y in [-2.2, -1.3])
upper = [v.co for v in vme.vertices if abs(v.co.x) < 0.15 and -1.8 <= v.co.y <= -1.2 and v.co.z > 2.0]
lower = [v.co for v in vme.vertices if abs(v.co.x) < 0.15 and -1.8 <= v.co.y <= -1.2 and v.co.z <= 2.0]
if upper and lower:
    print(f"Vehicle Mouth gap at Y=[-1.8,-1.2]: upper Z=[{min(p.z for p in upper):.3f},{max(p.z for p in upper):.3f}], lower Z=[{min(p.z for p in lower):.3f},{max(p.z for p in lower):.3f}]")
