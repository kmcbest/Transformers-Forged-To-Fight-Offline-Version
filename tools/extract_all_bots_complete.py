import UnityPy
import json
import os

search_dirs = [
    r"e:\Agent\TFTF\extracted_apk\assets\assetpack",
    r"e:\Agent\TFTF\extracted_apk\assets",
    r"e:\Agent\TFTF\assets_base",
    r"e:\Agent\TFTF\assets_netflix"
]

all_stages = {}

for s_dir in search_dirs:
    if not os.path.exists(s_dir): continue
    for root, dirs, files in os.walk(s_dir):
        for f in files:
            if not f.endswith(".assetbundle"): continue
            bundle_path = os.path.join(root, f)
            try:
                env = UnityPy.load(bundle_path)
                obj_dict = {o.path_id: o for o in env.objects}
                for obj in env.objects:
                    if obj.type.name == "GameObject":
                        tree = obj.read_typetree()
                        name = tree.get("m_Name", "")
                        lname = name.lower()
                        if "tformstage" in lname and ("special03" in lname or "special_03" in lname or "special3" in lname or "special_3" in lname or "attackspecial" in lname):
                            for c in tree.get("m_Component", []):
                                c_obj = obj_dict.get(c["component"]["m_PathID"])
                                if c_obj and c_obj.type.name == "MonoBehaviour":
                                    mb = c_obj.read_typetree()
                                    actors = mb.get("actorInfoList", [])
                                    actor0 = actors[0].get("actor_id") if actors else ""
                                    mdata_ref = mb.get("matineeData", {})
                                    mdata_obj = obj_dict.get(mdata_ref.get("m_PathID"))
                                    if mdata_obj:
                                        mdata_tree = mdata_obj.read_typetree()
                                        js = json.loads(mdata_tree.get("jSONData", "{}"))
                                        tracks = js.get("TRACKS", {})
                                        track_list = mdata_tree.get("trackList", [])
                                        
                                        dur = js.get("MC", {}).get("fc", 0) / js.get("MC", {}).get("pl", 30)
                                        actor_tracks = []
                                        for i in range(tracks.get("track_count", 0)):
                                            tr = tracks.get(f"track_{i}", {})
                                            if not isinstance(tr, dict): continue
                                            en = tr.get("en", "")
                                            eid = tr.get("eid", "")
                                            if "actor0" in eid.lower() or "locator" in eid.lower() or i < 15:
                                                if i < len(track_list):
                                                    for p in track_list[i].get("propertyList", []):
                                                        if p.get("propInfo", {}).get("infoName") == "m_Enabled":
                                                            curves_info = []
                                                            for crv in p.get("curves", []):
                                                                kfs = [(round(kf.get("time"), 3), round(kf.get("value"), 1)) for kf in crv.get("m_Curve", [])]
                                                                curves_info.append(kfs)
                                                            actor_tracks.append({
                                                                "track": i,
                                                                "en": en,
                                                                "eid": eid,
                                                                "curves": curves_info
                                                            })
                                        all_stages[name] = {
                                            "bundle": f,
                                            "actor0": actor0,
                                            "dur": round(dur, 3),
                                            "tracks": actor_tracks
                                        }
            except Exception:
                pass

print(f"Total SP3 stages across EVERYTHING: {len(all_stages)}")
with open(r"e:\Agent\TFTF\tools\all_stages_complete.json", "w", encoding="utf-8") as out_f:
    json.dump(all_stages, out_f, indent=2)
