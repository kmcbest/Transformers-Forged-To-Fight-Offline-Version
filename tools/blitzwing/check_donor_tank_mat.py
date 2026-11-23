import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env_d = UnityPy.load(str(DONOR_BUNDLE))
obj_map = {o.path_id: o for o in env_d.objects}

for smr_pid in [2138194849323017337, 4626197738286450028]:
    smr = obj_map[smr_pid].read_typetree()
    print(f"Donor Tank SMR {smr_pid} materials:")
    for m in smr.get('m_Materials', []):
        mpid = m.get('m_PathID')
        mat = obj_map[mpid].read_typetree()
        print(f"  PID {mpid}: '{mat.get('m_Name')}'")
        for env_k, env_v in mat['m_SavedProperties']['m_TexEnvs']:
            if env_k == '_base_tex':
                tex_pid = env_v['m_Texture']['m_PathID']
                tex = obj_map[tex_pid].read()
                print(f"    _base_tex: PID {tex_pid} '{tex.m_Name}'")
