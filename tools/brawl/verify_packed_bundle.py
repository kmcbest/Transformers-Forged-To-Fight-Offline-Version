import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import zipfile, io
from pathlib import Path
import UnityPy

APK_PATH = Path(r"E:\Agent\TFTF-blender\build\Transformers-9.2-offline-blender2.apk")
with zipfile.ZipFile(APK_PATH, "r") as z:
    bdata = z.read("assets/assetpack/brawl_gs_odr/brawl_gs.assetbundle")
    env = UnityPy.load(io.BytesIO(bdata))
    cab_files = list(env.file.files.keys())
    print("brawl_gs.assetbundle in APK size:", len(bdata))
    print("CAB files in bundle:", cab_files)
    ab_obj = next(o for o in env.objects if o.type.name == "AssetBundle")
    ab_tt = ab_obj.read_typetree()
    print("AssetBundle name:", ab_tt.get("m_Name"))
    print("AssetBundleName:", ab_tt.get("m_AssetBundleName"))
    print("Containers:", [c[0] for c in ab_tt.get("m_Container", [])])
