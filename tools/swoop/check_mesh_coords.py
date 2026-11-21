import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mesh_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\swoop_mesh.assetbundle")
env = UnityPy.load(str(mesh_bundle))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if name == "cha_swoop_gs_00":
            # get bounds
            box = tt.get("m_LocalAABB", {}).get("m_Center", {})
            extent = tt.get("m_LocalAABB", {}).get("m_Extent", {})
            print(f"Mesh {name}: Center={box}, Extent={extent}")
            # check vertices around chest forward (+Z in Unity is forward, +Y is up)
            # Or in donor Ramjet coordinate
            # Let's see bone bindposes if present
            bp = tt.get("m_BindPose", [])
            print(f"BindPose count: {len(bp)}")
            break
