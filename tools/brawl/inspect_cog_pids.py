import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

env = UnityPy.load(str(MEG_BUNDLE))
sf = list(env.assets)[0]

for pid, obj in sf.objects.items():
    if obj.type.name == "GameObject":
        tt = obj.read_typetree()
        if tt["m_Name"] == "COG":
            for comp in tt["m_Component"]:
                c_pid = comp["component"]["m_PathID"]
                c_obj = sf.objects.get(c_pid)
                if c_obj and c_obj.type.name == "Transform":
                    print(f"COG GO PID={pid}, Transform PID={c_pid}")

for pid in (-4076617426109914192, -2983655943056242676):
    smr_tt = sf.objects[pid].read_typetree()
    print(f"\nSMR PID={pid} RootBone: {smr_tt['m_RootBone']}")
    print(f"SMR PID={pid} m_Bones[21]: {smr_tt['m_Bones'][21]}")
