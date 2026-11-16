import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

env = UnityPy.load("assets_redeco/tarn_gs.assetbundle")
ab = next(o for o in env.objects if o.type.name == "AssetBundle").read()
print("Tarn m_Container:")
for k, v in ab.m_Container:
    print(f"  {k} -> preloadIndex={v.preloadIndex}, preloadSize={v.preloadSize}")
