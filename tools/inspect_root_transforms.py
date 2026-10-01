import UnityPy
from pathlib import Path

bundle_path = Path("toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle")
env = UnityPy.load(str(bundle_path))

game_objects = {}
transforms = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read()
        game_objects[obj.path_id] = data
    elif obj.type.name == "Transform":
        data = obj.read()
        transforms[obj.path_id] = data

for tid, trans in transforms.items():
    go_ref = trans.m_GameObject
    go = game_objects.get(go_ref.path_id)
    name = go.m_Name if go else "Unknown"
    parent_trans = transforms.get(trans.m_Father.path_id) if trans.m_Father.path_id else None
    parent_go = game_objects.get(parent_trans.m_GameObject.path_id) if parent_trans else None
    parent_name = parent_go.m_Name if parent_go else "None"
    if name in ["demolishor_prepared", "character_model", "cha_demolishor_gs_00", "Hips", "LeftArm", "LeftForeArm"]:
        print(f"Node: {name:20s} Parent: {parent_name:20s} rot={trans.m_LocalRotation} scale={trans.m_LocalScale} pos={trans.m_LocalPosition}")
