import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
mesh_dir = ROOT / "toolchain" / "unity_build_project" / "AssetBundles"

for p in mesh_dir.glob("*.assetbundle"):
    env = UnityPy.load(str(p))
    print(f"\n=== Bundle: {p.name} ===")
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            name = tt.get("m_Name")
            aabb = tt.get("m_LocalAABB", {})
            c = aabb.get("m_Center", {})
            e = aabb.get("m_Extent", {})
            if c and e:
                ymin = c["y"] - e["y"]
                ymax = c["y"] + e["y"]
                h = ymax - ymin
                print(f"  Mesh {name:30s}: Y=[{ymin:.3f}, {ymax:.3f}], H={h:.3f}, CenterY={c['y']:.3f}")
