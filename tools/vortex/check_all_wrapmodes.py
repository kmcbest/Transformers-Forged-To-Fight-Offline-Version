import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess, UnityPy
raw_head = subprocess.check_output(["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"], cwd=r"e:\Agent\TFTF-blender")
env_h = UnityPy.load(raw_head)
for o in env_h.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        print(f"  {tt['m_Name']} ({o.path_id}): WrapU={tt['m_TextureSettings']['m_WrapU']}, WrapV={tt['m_TextureSettings']['m_WrapV']}")
