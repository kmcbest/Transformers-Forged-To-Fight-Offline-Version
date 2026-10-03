import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

def get_path(go):
    parts = [go.m_Name]
    curr = go.m_Transform.read()
    while curr.m_Father.path_id != 0:
        parent_tr = curr.m_Father.read()
        parent_go = parent_tr.m_GameObject.read()
        parts.append(parent_go.m_Name)
        curr = parent_tr
    return "/".join(reversed(parts))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go = smr.m_GameObject.read()
        mesh_name = smr.m_Mesh.read().m_Name if smr.m_Mesh.path_id != 0 else "None"
        bones_count = len(smr.m_Bones)
        print(f"SMR GO: {go.m_Name}, Path: {get_path(go)}, Mesh: {mesh_name}, Bones: {bones_count}")
