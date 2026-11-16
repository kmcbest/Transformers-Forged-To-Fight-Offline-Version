import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env_d = UnityPy.load(str(DONOR_BUNDLE))

for o in env_d.objects:
    if o.path_id in (-4076617426109914192, -2983655943056242676):
        tt = o.read_typetree()
        root = tt.get('m_RootBone', {}).get('m_PathID')
        bone_21 = tt.get('m_Bones', [])[21].get('m_PathID')
        print(f"SMR {o.path_id}: RootBone={root}, Bone[21]={bone_21}, Matches: {root == bone_21}")
