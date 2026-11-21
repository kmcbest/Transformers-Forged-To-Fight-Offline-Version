import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
env = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "actorInfoList" in tt or "actorList" in tt or "actor_id" in str(tt):
            print(f"MonoBehaviour PID={o.path_id}: name={tt.get('m_Name')}")
            for k, v in tt.items():
                if "actor" in k.lower():
                    print(f"  {k}: {v}")
