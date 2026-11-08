import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ab_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle")
env = UnityPy.load(str(ab_path))
for obj in env.objects:
    if obj.type.name == "Mesh":
        m = obj.read()
        print(f"Mesh: {m.m_Name}")
        xs = [v[0] for v in m.m_Vertices]
        ys = [v[1] for v in m.m_Vertices]
        zs = [v[2] for v in m.m_Vertices]
        print(f"  X: [{min(xs):.2f}, {max(xs):.2f}] span={max(xs)-min(xs):.2f}")
        print(f"  Y: [{min(ys):.2f}, {max(ys):.2f}] span={max(ys)-min(ys):.2f}")
        print(f"  Z: [{min(zs):.2f}, {max(zs):.2f}] span={max(zs)-min(zs):.2f}")

