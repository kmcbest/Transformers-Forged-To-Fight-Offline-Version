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

for t_id, t in transforms.items():
    go_ptr = getattr(t, "m_GameObject", None)
    if go_ptr:
        go = gameobjects.get(go_ptr.path_id)
        if go and go.m_Name in ("zMerged", "Partition_0", "Environment"):
            pos = getattr(t, "m_LocalPosition", None)
            rot = getattr(t, "m_LocalRotation", None)
            scale = getattr(t, "m_LocalScale", None)
            print(f"{go.m_Name}: pos=({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}), rot=({rot.x:.3f}, {rot.y:.3f}, {rot.z:.3f}, {rot.w:.3f}), scale=({scale.x:.1f}, {scale.y:.1f}, {scale.z:.1f})")
