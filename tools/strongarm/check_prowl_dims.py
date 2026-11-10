import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import numpy as np

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if "00" in name and not "wpns" in name:
            aabb = tt.get("m_LocalAABB", {})
            print(f"Prowl robot mesh: {name}")
            print(f"  LocalAABB: m_Center={aabb.get('m_Center')}, m_Extent={aabb.get('m_Extent')}")
            # In Unity (Y-up, Z-fwd):
            # Center Y = extents * 2 is height
            m_c = aabb.get('m_Center', {})
            m_e = aabb.get('m_Extent', {})
            min_y = m_c.get('y', 0) - m_e.get('y', 0)
            max_y = m_c.get('y', 0) + m_e.get('y', 0)
            height = max_y - min_y
            print(f"  Unity Y (height) bounds: [{min_y:.4f}, {max_y:.4f}], height={height:.4f}m")
            min_x = m_c.get('x', 0) - m_e.get('x', 0)
            max_x = m_c.get('x', 0) + m_e.get('x', 0)
            print(f"  Unity X (width) bounds: [{min_x:.4f}, {max_x:.4f}], width={max_x-min_x:.4f}m")
            min_z = m_c.get('z', 0) - m_e.get('z', 0)
            max_z = m_c.get('z', 0) + m_e.get('z', 0)
            print(f"  Unity Z (depth) bounds: [{min_z:.4f}, {max_z:.4f}], depth={max_z-min_z:.4f}m")
            break
