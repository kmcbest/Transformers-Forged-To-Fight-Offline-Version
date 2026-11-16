import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
MESH_BUNDLE = BASE_DIR / r"toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle"
DONOR_BUNDLE = BASE_DIR / r"assets_base\megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"

print("=== 1. brawl_mesh.assetbundle ===")
env_m = UnityPy.load(str(MESH_BUNDLE))
for o in env_m.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh: {tt['m_Name']}")
        print(f"  BindPoses: {len(tt.get('m_BindPose', []))}")
        print(f"  BoneNameHashes: {len(tt.get('m_BoneNameHashes', []))}")
        print(f"  LocalAABB: {tt.get('m_LocalAABB')}")

print("\n=== 2. megatron_cin_rotf.assetbundle (Donor) ===")
env_d = UnityPy.load(str(DONOR_BUNDLE))
for o in env_d.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh PID={o.path_id} Name={tt['m_Name']}")
        print(f"  BindPoses: {len(tt.get('m_BindPose', []))}")
        print(f"  BoneNameHashes: {len(tt.get('m_BoneNameHashes', []))}")
    elif o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones_len = len(tt.get("m_Bones", []))
        root_bone = tt.get("m_RootBone", {}).get("m_PathID")
        enabled = tt.get("m_Enabled")
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        print(f"SMR PID={o.path_id} GO_PID={go_pid} Enabled={enabled} MeshPID={mesh_pid} BonesLen={bones_len} RootBone={root_bone}")

print("\n=== 3. brawl_gs.assetbundle (Current Output) ===")
env_b = UnityPy.load(str(BRAWL_BUNDLE))
for o in env_b.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh PID={o.path_id} Name={tt['m_Name']}")
        print(f"  BindPoses: {len(tt.get('m_BindPose', []))}")
        print(f"  BoneNameHashes: {len(tt.get('m_BoneNameHashes', []))}")
    elif o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones_len = len(tt.get("m_Bones", []))
        root_bone = tt.get("m_RootBone", {}).get("m_PathID")
        enabled = tt.get("m_Enabled")
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        print(f"SMR PID={o.path_id} GO_PID={go_pid} Enabled={enabled} MeshPID={mesh_pid} BonesLen={bones_len} RootBone={root_bone}")
