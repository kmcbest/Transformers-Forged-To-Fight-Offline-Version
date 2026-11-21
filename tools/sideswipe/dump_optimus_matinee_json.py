import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"

env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

matinee_obj = sf.objects[8781936353626196161]
tt = matinee_obj.read_typetree()
jdata = json.loads(tt.get("jSONData", "{}"))

print("Top level keys:", list(jdata.keys()))
tracks = jdata.get("TRACKS", {})
print(f"TRACKS type: {type(tracks)}")
if isinstance(tracks, dict):
    for k, v in list(tracks.items())[:10]:
        print(f"  k={k!r}, v_type={type(v)}, v={str(v)[:100]}")
elif isinstance(tracks, list):
    for idx, v in enumerate(tracks[:10]):
        print(f"  [{idx}] v_type={type(v)}, v={str(v)[:100]}")

# Search for character names in jdata
jstr = tt.get("jSONData", "")
for term in ["Optimus", "optimus", "Grindor", "grindor", "Barricade", "barricade", "Actor", "actor", "sideswipe", "Sideswipe"]:
    print(f"Occurrences of '{term}': {jstr.count(term)}")
