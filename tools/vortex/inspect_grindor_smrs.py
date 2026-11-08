import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

# Map GameObject PID -> name, components
gos = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        gos[obj.path_id] = (tree.get("m_Name", ""), tree.get("m_Components", []))

# Map Transform PID -> (go_id, father_id, children)
trans = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        father = tree.get("m_Father", {}).get("m_PathID")
        children = [c.get("m_PathID") for c in tree.get("m_Children", [])]
        trans[obj.path_id] = (go_id, father, children)

# Map SMR PID -> details
smrs = {}
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_id = tree.get("m_GameObject", {}).get("m_PathID")
        mesh_id = tree.get("m_Mesh", {}).get("m_PathID")
        mats = [m.get("m_PathID") for m in tree.get("m_Materials", [])]
        bones = [b.get("m_PathID") for b in tree.get("m_Bones", [])]
        smrs[obj.path_id] = (go_id, mesh_id, mats, len(bones))

# Map Material PID -> name
mats = {}
for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        mats[obj.path_id] = tree.get("m_Name", "")

# Map Mesh PID -> name
meshes = {}
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        meshes[obj.path_id] = tree.get("m_Name", "")

print("=== SMRs on Grindor ===")
for smr_id, (go_id, mesh_id, smr_mats, bone_count) in smrs.items():
    go_name = gos.get(go_id, ("unknown", []))[0]
    mesh_name = meshes.get(mesh_id, "None")
    mat_names = [f"{mats.get(m, 'unknown')}({m})" for m in smr_mats]
    print(f"SMR PID={smr_id} on GO='{go_name}' (GO_PID={go_id}): Mesh='{mesh_name}'({mesh_id}), Bones={bone_count}, Mats={mat_names}")
