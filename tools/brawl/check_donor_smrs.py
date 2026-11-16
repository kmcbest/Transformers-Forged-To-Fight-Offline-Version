import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env_d = UnityPy.load(str(donor_path))
f_d = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]

for pid in [-1713043385139994820, 6657504797783083318, -4076617426109914192, -2983655943056242676]:
    smr = f_d.objects[pid].read_typetree()
    mats = smr.get("m_Materials", [])
    print(f"Donor SMR {pid} ({smr.get('m_GameObject', {}).get('m_PathID')}): materials count={len(mats)}")
    for m in mats:
        print(f"   -> fid={m.get('m_FileID')}, pid={m.get('m_PathID')}")

mesh_robot_donor = f_d.objects[8927022796776742380].read_typetree()
print(f"Donor Robot Mesh submeshes: {len(mesh_robot_donor.get('m_SubMeshes', []))}")
mesh_veh_donor = f_d.objects[-9025351850097636016].read_typetree()
print(f"Donor Veh Mesh submeshes: {len(mesh_veh_donor.get('m_SubMeshes', []))}")
