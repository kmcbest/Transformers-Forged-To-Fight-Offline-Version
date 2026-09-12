import UnityPy

print("=== Searching moves.assetbundle ===")
env = UnityPy.load("extracted_apk/assets/assetpack/characters/moves.assetbundle")
for o in env.objects:
    try:
        data = o.read()
        name = getattr(data, "name", "") or getattr(data, "m_Name", "")
        if not name and hasattr(data, "read_typetree"):
            tree = data.read_typetree()
            name = tree.get("m_Name", "")
        if any(s in name.lower() for s in ["star", "thund", "warp", "seeker", "sideswipe", "bumblebee"]):
            print(f"[{o.type.name}] {name} (path_id={o.path_id})")
    except Exception as e:
        pass
