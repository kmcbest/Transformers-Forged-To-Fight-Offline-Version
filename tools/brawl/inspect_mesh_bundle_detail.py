import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"

env = UnityPy.load(str(MESH_BUNDLE))
sf = list(env.assets)[0]

for pid, obj in sf.objects.items():
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"\nMesh: '{tt['m_Name']}' (PID={pid})")
        print(f"  VertexCount: {tt['m_VertexData']['m_VertexCount']}")
        print(f"  SubMeshes ({len(tt['m_SubMeshes'])}):")
        for i, sm in enumerate(tt['m_SubMeshes']):
            print(f"    SubMesh[{i}]: firstByte={sm['firstByte']}, indexCount={sm['indexCount']}, topology={sm.get('topology')}")
        print(f"  BindPoses count: {len(tt.get('m_BindPose', []))}")
        print(f"  BoneNameHashes count: {len(tt.get('m_BoneNameHashes', []))}")
        print(f"  RootBoneNameHash: {tt.get('m_RootBoneNameHash')}")
        print(f"  LocalAABB: {tt.get('m_LocalAABB')}")
