import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import re
from pathlib import Path

asset_path = r'E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\cha_blitzwing_gs_00.asset'
txt = Path(asset_path).read_text(encoding='utf-8')

# Find m_LocalAABB
aabb_match = re.search(r'm_LocalAABB:\s*m_Center:\s*\{x:\s*([^,]+),\s*y:\s*([^,]+),\s*z:\s*([^}]+)\}\s*m_Extent:\s*\{x:\s*([^,]+),\s*y:\s*([^,]+),\s*z:\s*([^}]+)\}', txt)
if aabb_match:
    print("m_LocalAABB Center:", aabb_match.group(1), aabb_match.group(2), aabb_match.group(3))
    print("m_LocalAABB Extent:", aabb_match.group(4), aabb_match.group(5), aabb_match.group(6))

# Let's inspect first 10 vertices
v_match = re.search(r'm_Vertices:\s*\n(.*?)(?:\n  m_|\Z)', txt, re.DOTALL)
if v_match:
    lines = v_match.group(1).strip().split('\n')
    print(f"Total vertex lines: {len(lines)}")
    for l in lines[:5]:
        print(" ", l)

# Let's inspect bone weights
bw_match = re.search(r'm_BoneWeights:\s*\n(.*?)(?:\n  m_|\Z)', txt, re.DOTALL)
if bw_match:
    lines = bw_match.group(1).strip().split('\n')
    print(f"Total bone weight lines: {len(lines)}")
    for l in lines[:5]:
        print(" ", l)
