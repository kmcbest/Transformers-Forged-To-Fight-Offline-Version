import UnityPy
import json
import os

bundles_dir = r"e:\Agent\TFTF\extracted_apk\assets\assetpack"

results = {}

for folder in sorted(os.listdir(bundles_dir)):
    fpath = os.path.join(bundles_dir, folder)
    if not os.path.isdir(fpath): continue
    for f in os.listdir(fpath):
        if f.endswith(".assetbundle"):
            bpath = os.path.join(fpath, f)
            try:
                env = UnityPy.load(bpath)
                for obj in env.objects:
                    if obj.type.name == "MonoBehaviour":
                        raw = obj.read_typetree()
                        if "jSONData" in raw:
                            s = raw["jSONData"]
                            if "Special03" in s or "special_3" in s.lower() or "SpecialAttack03" in s:
                                bot_name = f.replace(".assetbundle", "")
                                mdata = json.loads(s)
                                mc = mdata.get("MC", {})
                                dur = mc.get("duration", 0)
                                tracks = mdata.get("TRACKS", {})
                                
                                # Find attach to transformed or transformed tracks
                                trans_events = []
                                hit_events = []
                                attach_events = []
                                
                                for k, v in tracks.items():
                                    if "econtainer" in k and isinstance(v, dict):
                                        for ek, ev in v.items():
                                            if isinstance(ev, dict):
                                                tt = ev.get("tt", "")
                                                et = ev.get("et", 0)
                                                if "HitEvent" in tt:
                                                    hit_events.append(et)
                                                if "Attach" in tt:
                                                    attach_events.append((et, ev.get("tn"), ev.get("pn")))
                                                if "transformed" in str(ev):
                                                    trans_events.append((et, ev))
                                
                                results[bot_name] = {
                                    "duration": dur,
                                    "hits": sorted(hit_events),
                                    "attaches": attach_events
                                }
            except Exception as e:
                pass

print(f"Parsed {len(results)} bots with SP3 Matinee!")
with open(r"e:\Agent\TFTF\tools\all_sp3_parsed.json", "w") as out:
    json.dump(results, out, indent=2)
print("Saved to e:\\Agent\\TFTF\\tools\\all_sp3_parsed.json")
