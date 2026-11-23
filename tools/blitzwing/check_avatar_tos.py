import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MEG_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(MEG_BUNDLE))

for o in env.objects:
    if o.type.name == "Avatar" and "00" in o.read_typetree().get("m_Name", ""):
        tt = o.read_typetree()
        tos = tt.get("m_TOS")
        print("TOS type:", type(tos))
        print("TOS sample:", tos[:10] if isinstance(tos, list) else list(tos.items())[:10])
