import json

with open(r"e:\Agent\TFTF\tools\actor0_sp3_tracks.json", "r") as f:
    data = json.load(f)

clean_timings = {}

for stage_name, sinfo in data.items():
    actor0 = sinfo["actor0"]
    dur = sinfo["dur"]
    tracks = sinfo["tracks"]
    
    # Find _01 track (transformed mesh) and _00 track (robot mesh)
    t01 = None
    t00 = None
    for tr in tracks:
        en = tr["en"].lower()
        if "_01" in en and not "wpns" in en and not "prop" in en and not "tape" in en:
            t01 = tr
        elif "_00" in en and not "wpns" in en and not "prop" in en and not "gun" in en:
            t00 = tr

    intervals = []
    if t01:
        # Extract intervals from t01 curves
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
    elif t00:
        # If no t01, extract inverse from t00 (when t00 is off)
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
                
    clean_timings[stage_name] = {
        "actor0": actor0,
        "bundle": sinfo["bundle"],
        "dur": dur,
        "intervals": intervals,
        "has_t01": t01 is not None,
        "has_t00": t00 is not None,
        "t01_name": t01["en"] if t01 else None,
        "t00_name": t00["en"] if t00 else None
    }

print(f"Total stages processed: {len(clean_timings)}")
for name, c in sorted(clean_timings.items()):
    print(f"{name} ({c['actor0']}): dur={c['dur']}s, intervals={c['intervals']}, t01={c['t01_name']}")

with open(r"e:\Agent\TFTF\tools\clean_sp3_intervals.json", "w") as out_f:
    json.dump(clean_timings, out_f, indent=2)
