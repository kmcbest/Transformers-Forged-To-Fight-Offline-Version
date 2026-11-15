import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        print(f"Texture2D PID={o.path_id}: '{tt['m_Name']}' {tt['m_Width']}x{tt['m_Height']} fmt={tt['m_TextureFormat']}")
