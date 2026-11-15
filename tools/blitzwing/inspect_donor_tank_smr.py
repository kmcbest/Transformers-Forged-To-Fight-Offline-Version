import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

donor_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(donor_bundle)
obj_map = {o.path_id: o for o in env.objects}

for pid in (2138194849323017337, 4626197738286450028):
    smr = obj_map.get(pid)
    if smr:
        tt = smr.read_typetree()
        print(f"\nOriginal Donor Tank SMR {pid}:")
        print("  RootBone:", tt.get("m_RootBone"))
        print("  Bones count:", len(tt.get("m_Bones", [])))
        print("  Materials:", tt.get("m_Materials"))
        print("  Enabled:", tt.get("m_Enabled"))
        print("  First 3 bones:", tt.get("m_Bones", [])[:3])
