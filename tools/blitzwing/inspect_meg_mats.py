import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"

env = UnityPy.load(str(bundle_path))
for o in env.objects:
    if o.path_id in (8075787426780741283, 1722215546450231611, 8175378592256487408, -9117353815363826346):
        d = o.read_typetree()
        print(f"\n=== Material PID {o.path_id} (name='{d.get('m_Name')}') ===")
        for tex_name, entry in d["m_SavedProperties"]["m_TexEnvs"]:
            pid = entry["m_Texture"]["m_PathID"]
            print(f"  Tex '{tex_name}': PID {pid}")
