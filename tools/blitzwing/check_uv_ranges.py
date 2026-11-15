import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import struct
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
mesh_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "blitzwing_mesh.assetbundle"

env = UnityPy.load(str(mesh_bundle))
for o in env.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if m['m_Name'] == 'cha_blitzwing_gs_00':
            # Stream 1 has UVs
            vd = m['m_VertexData']
            data = bytes(vd['m_DataSize']) # wait, _typelessdata or stream
            # Let's inspect submesh localAABB or UV min/max if possible
            for i, sm in enumerate(m['m_SubMeshes']):
                print(f"Submesh {i}: verts={sm['vertexCount']}, first={sm['firstVertex']}")
