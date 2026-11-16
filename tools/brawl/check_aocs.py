import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(donor_path))
sf = list(env.files.values())[0] if not hasattr(list(env.files.values())[0], 'files') else list(list(env.files.values())[0].files.values())[0]

for o in sf.objects.values():
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"AOC PID={o.path_id}: name='{tt.get('m_Name')}'")
