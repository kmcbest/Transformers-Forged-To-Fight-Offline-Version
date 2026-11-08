import UnityPy
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
print(f"Loading Grindor bundle: {bundle_path}")
env = UnityPy.load(bundle_path)

meshes = []
smrs = []
prefabs = []
anim_clips = []

for obj in env.objects:
    if obj.type.name == "Mesh":
        m = obj.read()
        mname = getattr(m, "m_Name", getattr(m, "name", ""))
        vc = getattr(m, "m_VertexCount", 0)
        meshes.append((mname, vc))
    elif obj.type.name == "SkinnedMeshRenderer":
        s = obj.read()
        mesh_obj = s.m_Mesh.read() if getattr(s, "m_Mesh", None) else None
        mesh_name = getattr(mesh_obj, "m_Name", getattr(mesh_obj, "name", "None")) if mesh_obj else "None"
        go_obj = s.m_GameObject.read() if getattr(s, "m_GameObject", None) else None
        go_name = getattr(go_obj, "m_Name", getattr(go_obj, "name", "None")) if go_obj else "None"
        bones_len = len(getattr(s, "m_Bones", []))
        smrs.append((go_name, mesh_name, bones_len))
    elif obj.type.name == "GameObject":
        g = obj.read()
        gname = getattr(g, "m_Name", getattr(g, "name", ""))
        if "prefab" in gname.lower() or "grindor" in gname.lower():
            prefabs.append(gname)

print("\n--- Grindor Meshes ---")
for name, vc in meshes:
    print(f"  Mesh: {name:35s} Verts: {vc}")

print("\n--- Grindor SMRs ---")
for go, mesh_name, bone_count in smrs:
    print(f"  GO: {go:35s} Mesh: {mesh_name:30s} Bones: {bone_count}")
