import glob
import os
import UnityPy
import json

# 1. Load all stages and their Actor0 expected name
bundles = glob.glob("extracted_apk/assets/assetpack/*/*.assetbundle")
bundles += glob.glob("assets_netflix/*.assetbundle")
bundles += glob.glob("assets_redeco/*.assetbundle")

stages_actor0 = {}

for bpath in set(bundles):
    try:
        env = UnityPy.load(bpath)
        obj_map = {obj.path_id: obj for obj in env.objects}
        for obj in env.objects:
            if obj.type.name == "GameObject":
                data = obj.read()
                if "TFormStage_" in data.m_Name and "Special03" in data.m_Name:
                    stage_name = data.m_Name
                    for comp in data.m_Components:
                        c_obj = obj_map.get(comp.path_id)
                        if not c_obj or c_obj.type.name != "MonoBehaviour": continue
                        tree = c_obj.read_typetree()
                        if "matineeData" in tree:
                            mdata_ref = tree.get("matineeData")
                            md_obj = obj_map.get(mdata_ref.get("m_PathID"))
                            if not md_obj: continue
                            md_tree = md_obj.read_typetree()
                            j = json.loads(md_tree.get("jSONData", "{}"))
                            tracks = j.get("TRACKS", {})
                            for k, v in tracks.items():
                                if isinstance(v, dict):
                                    eid = v.get("eid", "")
                                    if "|Actor0_locator" in eid:
                                        parts = eid.split("|")
                                        idx = parts.index("Actor0_locator")
                                        if idx > 0:
                                            expected = parts[idx - 1]
                                            # We want the character root model name, not weapon or transformed
                                            stages_actor0[stage_name] = expected
    except Exception as e:
        pass

# 2. Check each character bundle to see its prefab name and which special stage it references
char_bundles = glob.glob("extracted_apk/assets/assetpack/*/*.assetbundle")
char_bundles += glob.glob("assets_netflix/*.assetbundle")
char_bundles += glob.glob("assets_redeco/*.assetbundle")

bot_to_actor = {}

for bpath in set(char_bundles):
    bname = os.path.basename(bpath).replace(".assetbundle", "")
    try:
        env = UnityPy.load(bpath)
        obj_map = {obj.path_id: obj for obj in env.objects}
        prefab_name = None
        special_stage_name = None
        for obj in env.objects:
            if obj.type.name == "GameObject":
                data = obj.read()
                for comp in data.m_Components:
                    c_obj = obj_map.get(comp.path_id)
                    if not c_obj or c_obj.type.name != "MonoBehaviour": continue
                    tree = c_obj.read_typetree()
                    if "SpecialStagePrefab" in tree:
                        prefab_name = data.m_Name
                        sref = tree.get("SpecialStagePrefab")
                        if sref:
                            sobj = obj_map.get(sref.get("m_PathID"))
                            if sobj:
                                sdata = sobj.read()
                                special_stage_name = sdata.m_Name
        if prefab_name:
            expected = stages_actor0.get(special_stage_name, prefab_name)
            bot_to_actor[bname] = (prefab_name, special_stage_name, expected)
    except Exception as e:
        pass

print(f"Total mapped bots: {len(bot_to_actor)}")
for bname, (pname, sname, exp) in sorted(bot_to_actor.items()):
    print(f"'{bname}' -> prefab='{pname}', stage='{sname}', expected='{exp}'")
