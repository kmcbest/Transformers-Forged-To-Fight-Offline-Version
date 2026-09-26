import UnityPy
from pathlib import Path

p = Path("extracted_apk/assets/assetpack/primordial_base_odr/primordial_base.assetbundle")
env = UnityPy.load(str(p))

transforms = {}
gameobjects = {}

for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read()
        transforms[obj.path_id] = t
    elif obj.type.name == "GameObject":
        go = obj.read()
        gameobjects[obj.path_id] = go

print(f"Loaded {len(transforms)} transforms, {len(gameobjects)} gameobjects")

# Look for qb_base_top_01
for t_id, t in transforms.items():
    go_ptr = getattr(t, "m_GameObject", None)
    if go_ptr:
        go = gameobjects.get(go_ptr.path_id)
        if go and go.m_Name == "qb_base_top_01":
            print("Found qb_base_top_01!")
            def print_tree(cur_t, depth=0):
                c_go = gameobjects.get(cur_t.m_GameObject.path_id)
                pos = getattr(cur_t, "m_LocalPosition", None)
                pos_str = f"({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f})" if pos else ""
                print("  " * depth + f"{c_go.m_Name} pos={pos_str}")
                for child_ptr in getattr(cur_t, "m_Children", []):
                    child_t = transforms.get(child_ptr.path_id)
                    if child_t:
                        print_tree(child_t, depth + 1)
            print_tree(t)
            break
