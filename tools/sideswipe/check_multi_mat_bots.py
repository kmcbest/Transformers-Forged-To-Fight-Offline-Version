import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

apk_dir = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack")

multi_mat_bots = []
for bp in apk_dir.glob("*/*.assetbundle"):
    try:
        env = UnityPy.load(str(bp))
        for obj in env.objects:
            if obj.type.name == "SkinnedMeshRenderer":
                data = obj.read()
                if hasattr(data, 'm_Materials') and len(data.m_Materials) > 1:
                    multi_mat_bots.append((bp.parent.name, len(data.m_Materials)))
                    break
    except Exception:
        pass

print(f"Total bundles with multi-material SkinnedMeshRenderer: {len(multi_mat_bots)}")
for b, count in multi_mat_bots[:10]:
    print(f"  {b}: {count} materials")
