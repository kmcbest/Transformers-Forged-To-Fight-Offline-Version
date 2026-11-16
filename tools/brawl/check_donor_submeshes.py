import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\tarn_gs.assetbundle")
for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print("Tarn Mesh:", tt.get("m_Name"), "Submeshes:", len(tt.get("m_SubMeshes", [])))
    elif obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        print("Tarn SMR:", obj.path_id, "Materials count:", len(tt.get("m_Materials", [])))
