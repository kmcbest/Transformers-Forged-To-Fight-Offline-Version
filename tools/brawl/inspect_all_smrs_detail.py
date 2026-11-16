import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

def inspect_all_smrs(bundle_path, label):
    print(f"\n=== SMRs in {label}: {bundle_path.name} ===")
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    for pid, obj in sf.objects.items():
        if obj.type.name == "SkinnedMeshRenderer":
            tt = obj.read_typetree()
            go_pid = tt.get("m_GameObject", {}).get("m_PathID")
            go_obj = sf.objects.get(go_pid)
            go_name = go_obj.read_typetree().get("m_Name") if go_obj else "NULL"
            mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
            mesh_obj = sf.objects.get(mesh_pid)
            mesh_name = mesh_obj.read_typetree().get("m_Name") if mesh_obj else "NULL"
            submesh_count = len(mesh_obj.read_typetree().get("m_SubMeshes", [])) if mesh_obj else 0
            mats = tt.get("m_Materials", [])
            bones = tt.get("m_Bones", [])
            root_bone = tt.get("m_RootBone", {})
            print(f"SMR PID={pid} on GO '{go_name}':")
            print(f"  Mesh: '{mesh_name}' (PID={mesh_pid}), submeshes={submesh_count}")
            print(f"  Materials ({len(mats)}): {mats}")
            print(f"  Bones count: {len(bones)}, RootBone: {root_bone}")

inspect_all_smrs(MEG_BUNDLE, "MEGATRON")
inspect_all_smrs(BRAWL_BUNDLE, "BRAWL")
