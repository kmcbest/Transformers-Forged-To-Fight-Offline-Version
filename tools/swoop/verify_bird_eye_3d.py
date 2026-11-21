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

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
me = vh.data
uvl = me.uv_layers["UV0"].data

print("=== 1. Polys on Vehicle mapping to px=[600,690], py=[5,98] ===")
for p in me.polygons:
    pts = [uv_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
    cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
    if 600 <= cx <= 690 and 5 <= cy <= 98:
        rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
        if max(rgb) < 85:
            print(f"  cx={cx:5.1f} cy={cy:4.1f} 3D=({p.center.x:+.3f},{p.center.y:+.3f},{p.center.z:.3f}) n=({p.normal.x:+.2f},{p.normal.y:+.2f},{p.normal.z:+.2f}) rgb={rgb}")

print("\n=== 2. ALL Vehicle polys on Pteranodon Head (Z>2.35, -1.2<Y<-0.2, |X|>0.04) with max(rgb) < 115 or side-facing ===")
for p in me.polygons:
    if p.center.z > 2.35 and -1.20 < p.center.y < -0.25 and abs(p.center.x) > 0.04 and abs(p.normal.x) > 0.45:
        pts = [uv_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
        cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
        rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
        if max(rgb) < 120 and p.center.y > -0.90:
            print(f"  cx={cx:5.1f} cy={cy:5.1f} 3D=({p.center.x:+.3f},{p.center.y:+.3f},{p.center.z:.3f}) n=({p.normal.x:+.2f},{p.normal.y:+.2f},{p.normal.z:+.2f}) rgb={rgb}")
