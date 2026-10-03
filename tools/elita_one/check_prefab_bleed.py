import UnityPy

bundle_path = 'assets_redeco/elita_one_gs.assetbundle'
env = UnityPy.load(bundle_path)

# Build transform parent-child and go trees
tr_to_go = {}
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

# Find roots: Prefab 1 vs Prefab 2
# Let's find which transforms belong to which root
def find_root(tr_id):
    curr = tr_id
    visited = set()
    while curr and curr not in visited:
        visited.add(curr)
        tr = tr_dict.get(curr)
        if not tr: break
        father = tr.get('m_Father', {}).get('m_PathID')
        if not father or father == 0:
            return curr
        curr = father
    return curr

print("=== Checking SMR bones root parentage in elita_one_gs.assetbundle ===")
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        smr = obj.read_typetree()
        go_id = smr.get('m_GameObject', {}).get('m_PathID')
        go_name = go_dict.get(go_id, {}).get('m_Name', 'unknown')
        smr_tr_id = None
        for tid, gid in tr_to_go.items():
            if gid == go_id:
                smr_tr_id = tid
                break
        smr_root_tr = find_root(smr_tr_id)
        smr_root_name = go_dict.get(tr_to_go.get(smr_root_tr), {}).get('m_Name', 'unknown')
        
        bones = smr.get('m_Bones', [])
        bone_roots = set()
        for b in bones:
            b_tr_id = b.get('m_PathID')
            b_root = find_root(b_tr_id)
            b_root_name = go_dict.get(tr_to_go.get(b_root), {}).get('m_Name', 'unknown')
            bone_roots.add(b_root_name)
        
        print(f"SMR PID {obj.path_id} on '{go_name}':")
        print(f"  Owner root: '{smr_root_name}' (TR {smr_root_tr})")
        print(f"  Bones count: {len(bones)}")
        print(f"  Bones point to roots: {bone_roots}")
        if len(bone_roots) > 1 or (bone_roots and list(bone_roots)[0] != smr_root_name):
            print(f"  [!!!] DANGER: CROSS-PREFAB BONE BLEED DETECTED!")
