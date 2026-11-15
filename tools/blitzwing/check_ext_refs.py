import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

for sf in env.file.files.values():
    if hasattr(sf, "m_ExternalRefs"):
        for i, ref in enumerate(sf.m_ExternalRefs):
            print(f"  Ref [{i+1}]: assetPath='{ref.asset_path}'")
