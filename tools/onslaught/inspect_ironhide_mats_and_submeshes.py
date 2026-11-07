import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

print(f"=== INSPECTING {bundle_path.name} ===")
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mats = tree.get("m_Materials", [])
        mesh_ptr = tree.get("m_Mesh", {})
        print(f"\nSMR: m_Materials count = {len(mats)}")
        for i, mptr in enumerate(mats):
            for o2 in env.objects:
                if o2.path_id == mptr.get("m_PathID"):
                    print(f"  Material [{i}]: {o2.read_typetree().get('m_Name')}")
                    break
        # inspect the mesh
        for o2 in env.objects:
            if o2.path_id == mesh_ptr.get("m_PathID"):
                mtree = o2.read_typetree()
                submeshes = mtree.get("m_SubMeshes", [])
                print(f"  Mesh: {mtree.get('m_Name')}, Vertices: {mtree.get('m_VertexData', {}).get('m_VertexCount')}, SubMeshes count: {len(submeshes)}")
                break

print("\n=== ALL TEXTURES IN IRONHIDE BUNDLE ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        print(f"Texture2D: {tree.get('m_Name')}, Format: {tree.get('m_TextureFormat')}, Width: {tree.get('m_Width')}, Height: {tree.get('m_Height')}")

print("\n=== ALL MATERIALS IN IRONHIDE BUNDLE ===")
for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        print(f"Material: {tree.get('m_Name')}")
        tex_envs = tree.get("m_SavedProperties", {}).get("m_TexEnvs", [])
        for tex_prop in tex_envs:
            tex_ptr = tex_prop.get("second", {}).get("m_Texture", {})
            scale = tex_prop.get("second", {}).get("m_Scale", {})
            offset = tex_prop.get("second", {}).get("m_Offset", {})
            prop_name = tex_prop.get("first", {}).get("name", "")
            for o2 in env.objects:
                if o2.path_id == tex_ptr.get("m_PathID"):
                    print(f"    Prop: {prop_name} -> {o2.read_typetree().get('m_Name')} (scale={scale}, offset={offset})")
                    break
