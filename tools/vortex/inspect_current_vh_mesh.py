import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

ab_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle")
if not ab_path.exists():
    ab_path = Path(r"E:\Agent\TFTF-blender\tools\vortex\vortex_mesh.assetbundle")

print(f"Loading {ab_path}")
env = UnityPy.load(str(ab_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        data = obj.read_typetree()
        name = data.get("m_Name")
        if "01" in name or "vh" in name:
            print(f"Mesh: {name}")
            # AABB
            aabb = data.get("m_AABB", {})
            print(f"  Center: {aabb.get('m_Center')}")
            print(f"  Extent: {aabb.get('m_Extent')}")
            # Check bone weights count
            skin = data.get("m_Skin", [])
            print(f"  Skin entries: {len(skin)}")
