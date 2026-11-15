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
    if o.type.name == "Material":
        d = o.read_typetree()
        shader_pid = d.get("m_Shader", {}).get("m_PathID")
        print(f"Material PID={o.path_id:21d} | name='{d.get('m_Name')}' | shader_PID={shader_pid}")
