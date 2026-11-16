import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name")
        vcount = tt.get("m_VertexData", {}).get("m_VertexCount", 0)
        bones = tt.get("m_BoneNameHashes", [])
        bindposes = tt.get("m_BindPose", [])
        channels = tt.get("m_VertexData", {}).get("m_Channels", [])
        streams = tt.get("m_VertexData", {}).get("m_Streams", [])
        data_size = len(tt.get("m_VertexData", {}).get("m_DataSize", b""))
        print(f"\nMesh: {name}")
        print(f"  VertexCount: {vcount}")
        print(f"  Bones ({len(bones)}): {bones[:10]}...")
        print(f"  Bindposes count: {len(bindposes)}")
        print(f"  DataSize: {data_size} bytes")
        print(f"  Submeshes: {len(tt.get('m_SubMeshes', []))}")
        print(f"  Channels: {len(channels)}, Streams: {len(streams)}")
        for idx, s in enumerate(streams):
            print(f"    Stream[{idx}]: offset={s.get('offset')}, stride={s.get('stride')}, dividerOp={s.get('dividerOp')}")
