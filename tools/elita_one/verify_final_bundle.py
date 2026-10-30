import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
env = UnityPy.load(str(bundle_path))

for o in env.objects:
    if o.type.name == "Mesh" and o.read_typetree()["m_Name"] == "cha_arcee_gs_deluxe2014_00":
        t = o.read_typetree()
        vc = t["m_VertexData"]["m_VertexCount"]
        raw = bytes(t["m_VertexData"]["m_DataSize"])
        data = np.frombuffer(raw, dtype='<f4', count=vc * 10).reshape(vc, 10)
        pos = data[:, 0:3]
        norm = data[:, 3:6]
        tan = data[:, 6:10]
        idx = np.frombuffer(bytes(t["m_IndexBuffer"]), dtype='<u2')
        aabb = t.get("m_LocalAABB", {})
        
        print(f"=== cha_arcee_gs_deluxe2014_00 in Final AssetBundle ===")
        print(f"  Vertices: {vc}")
        print(f"  Indices: {len(idx)}")
        print(f"  First 12 indices: {idx[:12]}")
        print(f"  Pos X: [{pos[:, 0].min():.3f}, {pos[:, 0].max():.3f}]")
        print(f"  Pos Y: [{pos[:, 1].min():.3f}, {pos[:, 1].max():.3f}] (Height: {pos[:, 1].max() - pos[:, 1].min():.2f}m)")
        print(f"  Pos Z: [{pos[:, 2].min():.3f}, {pos[:, 2].max():.3f}]")
        print(f"  Normals length mean: {np.linalg.norm(norm, axis=1).mean():.4f}")
        print(f"  Tangents w values: {np.unique(tan[:, 3])}")
        print(f"  LocalAABB: Center={aabb.get('m_Center')}, Extent={aabb.get('m_Extent')}")
