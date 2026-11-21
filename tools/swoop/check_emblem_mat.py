import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env_m = UnityPy.load(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\swoop_mesh.assetbundle")
for o in env_m.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh '{tt['m_Name']}': verts={tt['m_VertexData']['m_VertexCount']} submeshes={len(tt['m_SubMeshes'])} bindposes={len(tt['m_BindPose'])}")
        for si, sm in enumerate(tt["m_SubMeshes"]):
            print(f"  SubMesh[{si}]: firstByte={sm['firstByte']} indexCount={sm['indexCount']} vertexCount={sm['vertexCount']}")

env_r = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env_r.objects}
for mid in (1469909421462177924, 3595971348910711679, 3520121911555544087):
    m = objs[mid].read_typetree()
    print(f"\nMaterial {mid} '{m['m_Name']}': shader={m['m_Shader']} keywords={m.get('m_ShaderKeywords')}")
