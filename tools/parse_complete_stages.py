import json

with open(r"e:\Agent\TFTF\tools\all_stages_complete.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total stages: {len(data)}\n")

results = {}

for sname, sinfo in sorted(data.items()):
    actor0 = sinfo["actor0"]
    dur = sinfo["dur"]
    tracks = sinfo["tracks"]
    
    t01 = None
    t00 = None
    for tr in tracks:
        en = tr["en"].lower()
        if "_01" in en and not any(w in en for w in ["wpns", "prop", "tape", "gun", "sword"]):
            t01 = tr
        elif "_00" in en and not any(w in en for w in ["wpns", "prop", "tape", "gun", "sword"]):
            t00 = tr
            
    intervals = []
    if t01 and t01["curves"]:
        for crv in t01["curves"]:
            t_on = None
            for t, v in crv:
                if v >= 0.5 and t_on is None:
                    t_on = t
                elif v < 0.5 and t_on is not None:
                    intervals.append([round(t_on, 3), round(t, 3)])
                    t_on = None
            if t_on is not None:
                intervals.append([round(t_on, 3), round(dur, 3)])
    elif t00 and t00["curves"]:
        for crv in t00["curves"]:
            t_off = None
            for t, v in crv:
                if v < 0.5 and t_off is None:
                    t_off = t
                elif v >= 0.5 and t_off is not None:
                    intervals.append([round(t_off, 3), round(t, 3)])
                    t_off = None
            if t_off is not None:
                intervals.append([round(t_off, 3), round(dur, 3)])
                
    results[sname] = {
        "actor0": actor0,
        "bundle": sinfo["bundle"],
        "dur": dur,
        "intervals": intervals,
        "t01": t01["en"] if t01 else None,
        "t00": t00["en"] if t00 else None
    }
    
    ms_ivs = [[int(round(s * 1000)), int(round(e * 1000))] for s, e in intervals]
    print(f"{sname:<42} | actor0: {actor0:<28} | dur: {dur:5.2f}s | ivs: {str(ms_ivs):<25} | t01: {str(t01['en'] if t01 else None)}")

with open(r"e:\Agent\TFTF\tools\complete_sp3_intervals.json", "w", encoding="utf-8") as out_f:
    json.dump(results, out_f, indent=2)
