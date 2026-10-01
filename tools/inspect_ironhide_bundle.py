import UnityPy
import glob

# Search for ironhide bundle
ironhide_bundles = glob.glob("**/ironhide_cin_rotf*.assetbundle", recursive=True) + glob.glob("**/ironhide*.assetbundle", recursive=True)
print("Ironhide bundles found:", ironhide_bundles)

if ironhide_bundles:
    env = UnityPy.load(ironhide_bundles[0])
    game_objects = {}
    transforms = {}
    for obj in env.objects:
        if obj.type.name == "GameObject":
            game_objects[obj.path_id] = obj.read()
        elif obj.type.name == "Transform":
            transforms[obj.path_id] = obj.read()
    
    for tid, trans in transforms.items():
        go_ref = trans.m_GameObject
        go = game_objects.get(go_ref.path_id)
        name = go.m_Name if go else "Unknown"
        parent_trans = transforms.get(trans.m_Father.path_id) if trans.m_Father.path_id else None
        parent_go = game_objects.get(parent_trans.m_GameObject.path_id) if parent_trans else None
        parent_name = parent_go.m_Name if parent_go else "None"
        if name in ["character_model", "Hips", "cha_ironhide_cin_rotf_00"] or parent_name == "None":
            print(f"Ironhide Node: {name:25s} Parent: {parent_name:25s} rot={trans.m_LocalRotation} scale={trans.m_LocalScale} pos={trans.m_LocalPosition}")
