import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env_d = UnityPy.load(str(donor_path))
sf = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]

found_anim = 0
for o in sf.objects.values():
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        s = str(tt)
        if "-7777457830161264517" in s or "-7854615674899395621" in s:
            print(f"AnimationClip {o.path_id} references mat!")
            found_anim += 1

print(f"Total animation clips referencing those mats: {found_anim}")
