import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)
obj_map = {o.path_id: o for o in env.objects}

mesh = obj_map.get(8396146535644667895)
if mesh:
    tt = mesh.read_typetree()
    print("Tank Mesh Name:", tt.get("m_Name"))
    print("  SubMeshes count:", len(tt.get("m_SubMeshes", [])))
    print("  SubMeshes:", tt.get("m_SubMeshes"))
    print("  LocalAABB:", tt.get("m_LocalAABB"))
    print("  IndexBuffer len:", len(tt.get("m_IndexBuffer", b"")))
    print("  VertexData VertexCount:", tt.get("m_VertexData", {}).get("m_VertexCount"))
    print("  VertexData DataSize len:", len(tt.get("m_VertexData", {}).get("m_DataSize", b"")))
    print("  BoneNameHashes:", tt.get("m_BoneNameHashes"))
    print("  BindPose len:", len(tt.get("m_BindPose", [])))
