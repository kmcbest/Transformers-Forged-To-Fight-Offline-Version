import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path("E:/Agent/TFTF/assets_ios/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for pid in (2138194849323017337, 4626197738286450028):
    smr = obj_map[pid].read_typetree()
    mesh_pid = smr["m_Mesh"]["m_PathID"]
    mesh = obj_map[mesh_pid].read_typetree()
    print(f"\nMegatron Tank SMR PID {pid}:")
    print(f"  Mesh PID: {mesh_pid}, Name: '{mesh.get('m_Name')}'")
    print(f"  RootBone: {smr.get('m_RootBone')}")
    print(f"  Bones: {smr.get('m_Bones')}")
    print(f"  Mesh BoneNameHashes ({len(mesh.get('m_BoneNameHashes'))}): {mesh.get('m_BoneNameHashes')[:5]}...")
    print(f"  Mesh BindPose count: {len(mesh.get('m_BindPose'))}")
    print(f"  Mesh BonesAABB count: {len(mesh.get('m_BonesAABB'))}")
    print(f"  Mesh LocalAABB: {mesh.get('m_LocalAABB')}")
