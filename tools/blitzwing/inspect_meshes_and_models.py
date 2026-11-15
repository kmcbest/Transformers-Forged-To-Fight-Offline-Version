import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

# 1. Inspect cha_blitzwing_gs_00.asset
bw_asset_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Blitzwing" / "cha_blitzwing_gs_00.asset"
print("Checking cha_blitzwing_gs_00.asset exists:", bw_asset_path.exists())
if bw_asset_path.exists():
    env = UnityPy.load(str(bw_asset_path))
    for o in env.objects:
        if o.type.name == "Mesh":
            m = o.read_typetree()
            print(f"[Mesh in cha_blitzwing_gs_00.asset] name='{m['m_Name']}', verts={m['m_VertexData']['m_VertexCount']}, submeshes={len(m['m_SubMeshes'])}, bindposes={len(m['m_BindPose'])}")

# 2. Inspect Megatron donor bundle
meg_donor = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
print("\nChecking Megatron donor bundle:", meg_donor.exists())
if meg_donor.exists():
    env_meg = UnityPy.load(str(meg_donor))
    for o in env_meg.objects:
        if o.type.name == "Mesh":
            m = o.read_typetree()
            print(f"[Donor Mesh] PID={o.path_id}, name='{m['m_Name']}', verts={m['m_VertexData']['m_VertexCount']}, submeshes={len(m['m_SubMeshes'])}, bones={len(m['m_BoneNameHashes'])}")
        elif o.type.name == "SkinnedMeshRenderer":
            smr = o.read_typetree()
            go_pid = smr["m_GameObject"]["m_PathID"]
            mesh_pid = smr["m_Mesh"]["m_PathID"] if "m_Mesh" in smr else None
            mats = [mat["m_PathID"] for mat in smr.get("m_Materials", [])]
            print(f"[Donor SMR] PID={o.path_id}, mesh_PID={mesh_pid}, mats={mats}, bones={len(smr.get('m_Bones', []))}")
