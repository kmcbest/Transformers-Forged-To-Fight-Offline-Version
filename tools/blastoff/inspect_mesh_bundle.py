import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import UnityPy
import numpy as np
from pathlib import Path
from tools.validate_port_gates import parse_unity_mesh_streams

mb_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle")
env = UnityPy.load(str(mb_path))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh name: {tt['m_Name']}")
        pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
        print(f"  vc={len(pts)}")
        print(f"  X min={pts[:,0].min():.4f}, max={pts[:,0].max():.4f}")
        print(f"  Y min={pts[:,1].min():.4f}, max={pts[:,1].max():.4f}")
        print(f"  Z min={pts[:,2].min():.4f}, max={pts[:,2].max():.4f}")
        print(f"  raw bounds: {tt.get('m_LocalAABB')}")
