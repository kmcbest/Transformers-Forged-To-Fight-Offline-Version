import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

TARGET = Path("assets_redeco/blastoff_gs.assetbundle")
print(f"Target exists: {TARGET.exists()} (size: {TARGET.stat().st_size})")

env = UnityPy.load(str(TARGET))
print(f"File keys: {list(env.file.files.keys())}")
for f in env.file.files.values():
    if hasattr(f, "objects"):
        print(f"SerializedFile: {getattr(f, 'name', '')}")
        for o in f.objects.values():
            if o.type.name == "AssetBundle":
                tt = o.read_typetree()
                print("AssetBundle name:", tt.get("m_Name"))
                print("AssetBundle container:", tt.get("m_Container"))
