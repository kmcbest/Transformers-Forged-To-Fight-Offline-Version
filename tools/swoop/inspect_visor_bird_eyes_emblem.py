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

def uv_to_px_box(uvs):
    xs = [np.clip(u.x, 0, 0.9999) * tw for u in uvs]
    ys = [np.clip(1.0 - u.y, 0, 0.9999) * th for u in uvs]
    return min(xs), max(xs), min(ys), max(ys)

def body_atlas_uv_to_src(u, v):
    return (u - 0.004) / (0.746 - 0.004), (v - 0.254) / (0.996 - 0.254)

# 1. Inspect Symbol_AB materials & dims in Swoop_pbr.fbx
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sym = bpy.data.objects.get("Symbol_AB")
if sym:
    me = sym.data
    print("=== Raw Symbol_AB materials & bounds ===")
    for mi, m in enumerate(me.materials):
        mpolys = [p for p in me.polygons if p.material_index == mi]
        mpts = [me.vertices[vi].co for p in mpolys for vi in p.vertices]
        if mpts:
            print(f"  Mat[{mi}] '{m.name}': polys={len(mpolys)} local X=[{min(p.x for p in mpts):.5f},{max(p.x for p in mpts):.5f}] Y=[{min(p.y for p in mpts):.5f},{max(p.y for p in mpts):.5f}] Z=[{min(p.z for p in mpts):.5f},{max(p.z for p in mpts):.5f}]")
    # Also check evaluated world bounds (with Bip001 pose) of each material
    deps = bpy.context.evaluated_depsgraph_get()
    sym_ev = sym.evaluated_get(deps).data
    for mi, m in enumerate(me.materials):
        mpolys = [p for p in sym_ev.polygons if p.material_index == mi]
        mpts = [sym.matrix_world @ sym_ev.vertices[vi].co for p in mpolys for vi in p.vertices]
        if mpts:
            print(f"  Posed World Mat[{mi}] '{m.name}': X=[{min(p.x for p in mpts):.5f},{max(p.x for p in mpts):.5f}] Y=[{min(p.y for p in mpts):.5f},{max(p.y for p in mpts):.5f}] Z=[{min(p.z for p in mpts):.5f},{max(p.z for p in mpts):.5f}]")

# 2. Inspect swoop_prepared.fbx Chest Beak surface front Y vs X/Z, and Robot Visor UV box!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data
uvl = me.uv_layers["UV0"].data

print("\n=== Chest Beak Surface Front (min Y) across Z in [5.5, 9.0], |X| < 0.45 ===")
for z0 in np.arange(5.5, 9.0, 0.25):
    pts = [v.co for v in me.vertices if abs(v.co.x) < 0.45 and z0 <= v.co.z < z0 + 0.25 and v.co.y < -0.5]
    if pts:
        # find frontmost point near X=0
        front_c = [p for p in pts if abs(p.x) < 0.25]
        fy = min(p.y for p in front_c) if front_c else min(p.y for p in pts)
        print(f"  Z=[{z0:.2f},{z0+0.25:.2f}): frontmost Y(near X=0) = {fy:+.4f}, min_all_Y = {min(p.y for p in pts):+.4f}")

# Robot Visor exact UV polygon mask
visor_polys = []
for p in me.polygons:
    if p.normal.y < -0.2 and 10.10 <= p.center.z <= 10.33 and abs(p.center.x) < 0.32 and p.center.y < -0.30:
        uvs = [body_atlas_uv_to_src(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
        cu = sum(u[0] for u in uvs)/len(uvs); cv = sum(u[1] for u in uvs)/len(uvs)
        px = int(np.clip(cu, 0, 0.9999) * tw); py = int(np.clip(1.0 - cv, 0, 0.9999) * th)
        rgb = tex[py, px]
        # Dark grey visor: r<80, g<80, b<80, neutral (max-min < 20)
        if max(rgb) < 85 and (int(max(rgb)) - int(min(rgb))) < 20:
            x0, x1, y0, y1 = uv_to_px_box([type('UV', (), {'x': u[0], 'y': u[1]})() for u in uvs])
            visor_polys.append((p.index, x0, x1, y0, y1, p.center.x, p.center.z))

if visor_polys:
    print(f"\n=== Robot Visor Dark Polys: count={len(visor_polys)} ===")
    print(f"  1024x1024 exact UV bounds: x=[{min(v[1] for v in visor_polys):.2f}, {max(v[2] for v in visor_polys):.2f}], y=[{min(v[3] for v in visor_polys):.2f}, {max(v[4] for v in visor_polys):.2f}]")
    print(f"  3D X=[{min(v[5] for v in visor_polys):+.3f}, {max(v[5] for v in visor_polys):+.3f}], Z=[{min(v[6] for v in visor_polys):.3f}, {max(v[6] for v in visor_polys):.3f}]")

# Check any neighbor pixels around visor in Tx_Swoop_D_RGB
sub = tex[648:672, 888:952]
is_dark_visor = (sub.max(axis=2) < 85) & ((sub.max(axis=2).astype(int) - sub.min(axis=2).astype(int)) < 20)
dys, dxs = np.where(is_dark_visor)
print(f"  Tx_Swoop_D_RGB dark visor island in [888:952, 648:672]: px=[{888+dxs.min()},{888+dxs.max()}], py=[{648+dys.min()},{648+dys.max()}], count={len(dxs)}")

# 3. Inspect Vehicle Pteranodon Head Eyes!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
vme = vh.data
vuvl = vme.uv_layers.active.data
print("\n=== Pteranodon Dark Eye Clusters (Z in [2.35, 2.75], Y in [-1.1, -0.6], |X| in [0.08, 0.25]) ===")
vh_eye_polys = []
for p in vme.polygons:
    if 2.30 <= p.center.z <= 2.75 and -1.15 <= p.center.y <= -0.60 and 0.05 <= abs(p.center.x) <= 0.30:
        uvs = [body_atlas_uv_to_src(vuvl[li].uv.x, vuvl[li].uv.y) for li in p.loop_indices]
        cu = sum(u[0] for u in uvs)/len(uvs); cv = sum(u[1] for u in uvs)/len(uvs)
        px = int(np.clip(cu, 0, 0.9999) * tw); py = int(np.clip(1.0 - cv, 0, 0.9999) * th)
        rgb = tuple(int(c) for c in tex[py, px])
        x0, x1, y0, y1 = uv_to_px_box([type('UV', (), {'x': u[0], 'y': u[1]})() for u in uvs])
        if max(rgb) < 95 and abs(rgb[0] - rgb[2]) < 20:
            vh_eye_polys.append((p.index, x0, x1, y0, y1, p.center.x, p.center.y, p.center.z, rgb))

if vh_eye_polys:
    print(f"  Pteranodon dark head polys: count={len(vh_eye_polys)}")
    # Group Left vs Right (px < 930 vs px >= 930)
    for side, filt in (("Left/Right A (px<930)", [v for v in vh_eye_polys if v[1] < 930]), ("Left/Right B (px>=930)", [v for v in vh_eye_polys if v[1] >= 930])):
        if filt:
            print(f"  {side}: polys={len(filt)} px=[{min(v[1] for v in filt):.2f},{max(v[2] for v in filt):.2f}] py=[{min(v[3] for v in filt):.2f},{max(v[4] for v in filt):.2f}] X=[{min(v[5] for v in filt):+.3f},{max(v[5] for v in filt):+.3f}] Y=[{min(v[6] for v in filt):.3f},{max(v[6] for v in filt):.3f}] Z=[{min(v[7] for v in filt):.3f},{max(v[7] for v in filt):.3f}] sampleRGB={filt[0][8]}")
            # Also check actual dark pixels around this region in Tx_Swoop_D_RGB
            px0 = max(0, int(min(v[1] for v in filt)) - 5); px1 = min(tw, int(max(v[2] for v in filt)) + 6)
            py0 = max(0, int(min(v[3] for v in filt)) - 5); py1 = min(th, int(max(v[4] for v in filt)) + 6)
            patch = tex[py0:py1, px0:px1]
            dk = (patch.max(axis=2) < 90) & ((patch.max(axis=2).astype(int) - patch.min(axis=2).astype(int)) < 20)
            ys2, xs2 = np.where(dk)
            if len(xs2) > 0:
                print(f"    Tx_Swoop_D_RGB dark island in [{px0}:{px1}, {py0}:{py1}]: px=[{px0+xs2.min()},{px0+xs2.max()}], py=[{py0+ys2.min()},{py0+ys2.max()}], count={len(xs2)}")
