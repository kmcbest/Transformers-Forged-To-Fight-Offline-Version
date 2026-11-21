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

# Root stage GO
STAGE_ROOT = 3256447252977910551
stage_obj = sf.objects[STAGE_ROOT]
print(f"Stage Root: {stage_obj.type.name}, name={stage_obj.read_typetree().get('m_Name')}")

for pid, o in sf.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "jSONData" in tt:
            print(f"\nMatineeData PID={pid}, name={tt.get('m_Name')}")
            try:
                data = json.loads(tt.get("jSONData"))
                print(f"  Tracks count: {len(data.get('tracks', {}))}")
                for tname, tr in data.get("tracks", {}).items():
                    print(f"    {tname}: type={tr.get('type')}, target={tr.get('targetName', tr.get('target'))}")
            except Exception as e:
                print(f"  Error parsing jSONData: {e}")
        elif "actorInfoList" in tt:
            print(f"\nTFormMatineeStage PID={pid}, name={tt.get('m_Name')}")
            for a in tt.get("actorInfoList", []):
                print(f"  Actor: {a}")
        elif "m_Events" in tt:
            print(f"\nAudio/Events PID={pid}, name={tt.get('m_Name')}")
