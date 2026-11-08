import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

# Check vortex_vh_prepared.fbx or asset
p_asset = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\cha_vortex_vh_grafted.asset")
# Read vertex data from YAML
with open(p_asset, "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect localAABB
for line in text.splitlines():
    if "m_Center:" in line or "m_Extent:" in line:
        print(line)

