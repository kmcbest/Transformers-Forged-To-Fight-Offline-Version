import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy

ROOT = Path(r"E:\Agent\TFTF-blender")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data
uv1 = me.uv_layers["UVMap"].data
sym_polys = [p for p in me.polygons if all(uv1[li].uv.x >= 0.75 for li in p.loop_indices)]
print(f"Symbol polys in UVMap (u>=0.75): count={len(sym_polys)}")
if sym_polys:
    pts = [me.vertices[vi].co for p in sym_polys for vi in p.vertices]
    print(f"  3D coords: X=[{min(p.x for p in pts):.4f},{max(p.x for p in pts):.4f}] Y=[{min(p.y for p in pts):.4f},{max(p.y for p in pts):.4f}] Z=[{min(p.z for p in pts):.4f},{max(p.z for p in pts):.4f}]")
    # Also check nearest beak surface Y at center (X~0, Z~center)
    cz = (min(p.z for p in pts) + max(p.z for p in pts)) / 2
    beak_pts = [v.co for v in me.vertices if abs(v.co.x) < 0.25 and abs(v.co.z - cz) < 0.25 and v.co.y < -0.2]
    print(f"  At Z={cz:.3f}, Chest beak Y=[{min(p.y for p in beak_pts):.4f}, {max(p.y for p in beak_pts):.4f}]")
