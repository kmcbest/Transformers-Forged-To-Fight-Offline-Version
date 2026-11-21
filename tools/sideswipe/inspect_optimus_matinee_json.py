import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
env_op = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))
md_obj = [o for o in env_op.objects if o.path_id == 8781936353626196161][0]
tt = md_obj.read_typetree()
jdata = json.loads(tt["jSONData"])
tracks = jdata["TRACKS"]

# Group by track index
track_dict = {}
for k, v in tracks.items():
    if k.startswith("track_"):
        parts = k.split("_")
        if parts[1].isdigit():
            t_idx = int(parts[1])
            sub_k = "_".join(parts[2:])
            track_dict.setdefault(t_idx, {})[sub_k] = v

print(f"Total structured tracks: {len(track_dict)}")
for idx in sorted(track_dict.keys()):
    t = track_dict[idx]
    print(f"Track {idx:02d}: en='{t.get('en', '')}', enp='{t.get('enp', '')}', teoacn='{t.get('teoacn', '')}', eid='{t.get('eid', '')}'")
