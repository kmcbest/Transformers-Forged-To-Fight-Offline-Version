import UnityPy

env = UnityPy.load("assets_redeco/character_audio.assetbundle")
obj_map = {obj.path_id: obj for obj in env.objects}

for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if name.endswith("_frl"):
            for comp_ref in tree.get("m_Component", []):
                comp = obj_map.get(comp_ref["component"]["m_PathID"])
                if comp and comp.type.name == "MonoBehaviour":
                    ctree = comp.read_typetree()
                    if "_volume" in ctree:
                        print(f"{name:25}: volume={ctree['_volume']:.4f}, p_rand={ctree['_pitchRandomization']:.4f}, v_rand={ctree['_volumeRandomization']:.4f}")
