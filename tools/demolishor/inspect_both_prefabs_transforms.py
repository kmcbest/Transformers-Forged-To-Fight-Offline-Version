import UnityPy

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# Map transform to gameobject
tr_to_go = {}
go_to_tr = {}
go_dict = {}
tr_dict = {}

for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_dict[obj.path_id] = tree
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

def get_prefab_transforms(root_go_id):
    result = {}
    def recurse(go_id):
        go = go_dict.get(go_id)
        if not go: return
        name = go.get('m_Name')
        tr_id = go_to_tr.get(go_id)
        if "chop" not in name and name not in result:
            result[name] = tr_id
        tr = tr_dict.get(tr_id)
        if tr:
            for child in tr.get('m_Children', []):
                c_tr_id = child.get('m_PathID')
                c_go_id = tr_to_go.get(c_tr_id)
                recurse(c_go_id)
    recurse(root_go_id)
    return result

p1_transforms = get_prefab_transforms(8887288183430146843)
p2_transforms = get_prefab_transforms(-4129943903446534184)

print(f"Prefab 1 (ironhide_cin_rotf.prefab) has {len(p1_transforms)} named transforms.")
print(f"Prefab 2 (ironhide_cin_rotf_lw.prefab) has {len(p2_transforms)} named transforms.")

# Check if both have Hips, Spine, RightArm, LeftArm
for b in ["Hips", "Spine", "RightArm", "LeftArm", "Head"]:
    print(f"  {b}: P1={p1_transforms.get(b)}, P2={p2_transforms.get(b)}")
