from __future__ import annotations
import copy
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "build" / "showcase_bundle_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def patch_character_bundle(data: bytes, bname: str) -> bytes:
    h = hashlib.md5(data).hexdigest()[:12]
    cache_file = CACHE_DIR / f"{bname}.{h}.assetbundle"
    if cache_file.exists():
        return cache_file.read_bytes()

    try:
        import UnityPy
        env = UnityPy.load(data)
        fight_ctrl_pid = None

        # 1. Find AnimatorOverrideController with "fight"
        for obj in env.objects:
            if obj.type.name == "AnimatorOverrideController":
                tree = obj.read_typetree()
                if "fight" in tree.get("m_Name", "").lower():
                    fight_ctrl_pid = obj.path_id
                    break

        if not fight_ctrl_pid:
            return data

        # 2. Add "fight" prop to PropsController on _lw.prefab pointing to fight AOC
        prop_added = False
        for obj in env.objects:
            if obj.type.name == "MonoBehaviour":
                tree = obj.read_typetree()
                if "_props" in tree:
                    props = tree.get("_props", {})
                    keys = props.get("_serializedKeys", [])
                    vals = props.get("_serializedValues", [])
                    if len(vals) > 0 and "fight" not in keys:
                        template_prop = copy.deepcopy(vals[0])
                        template_prop["Name"] = "fight"
                        template_prop["PropType"] = 0
                        template_prop["InitFlags"] = 0
                        template_prop["RootPath"] = ""
                        template_prop["PrefabAssetGUID"] = ""
                        template_prop["OverrideController"] = {"m_FileID": 0, "m_PathID": fight_ctrl_pid}
                        template_prop["PositionOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                        template_prop["RotationOffset"] = {"x": 0.0, "y": 0.0, "z": 0.0}
                        template_prop["Scale"] = {"x": 1.0, "y": 1.0, "z": 1.0}
                        template_prop["_instance"] = {"m_FileID": 0, "m_PathID": 0}
                        template_prop["_animator"] = {"m_FileID": 0, "m_PathID": 0}
                        template_prop["_renderers"] = []
                        keys.append("fight")
                        vals.append(template_prop)
                        props["_serializedKeys"] = keys
                        props["_serializedValues"] = vals
                        tree["_props"] = props
                        obj.save_typetree(tree)
                        prop_added = True
                        break

        # 3. Patch animator_char_fight in this bundle if present
        for obj in env.objects:
            if obj.type.name == "AnimatorController":
                tree = obj.read_typetree()
                if "fight" in tree.get("m_Name", "").lower():
                    tos = dict(tree.get("m_TOS", []))
                    data_dict = tree.get("m_Controller", {}).get("m_StateMachineArray", [])
                    if data_dict:
                        sm_data = data_dict[0].get("data", {})
                        states = sm_data.get("m_StateConstantArray", [])
                        for s_wrap in states:
                            s = s_wrap.get("data", {})
                            nid = s.get("m_NameID")
                            sname = tos.get(nid)
                            if sname in ["SpecialAttack01", "SpecialAttack02"]:
                                for t_wrap in s.get("m_TransitionConstantArray", []):
                                    t = t_wrap.get("data", {})
                                    t["m_HasExitTime"] = True
                                    t["m_ExitTime"] = 0.95
                                    t["m_TransitionDuration"] = 0.25
                                    t["m_ConditionConstantArray"] = []
                    obj.save_typetree(tree)

        patched = env.file.save()
        cache_file.write_bytes(patched)
        print(f"[*] Patched showcase bundle (AOC linked in props): {bname}")
        return patched
    except Exception as e:
        print(f"Warning: Failed to patch character bundle {bname}: {e}")
        return data
