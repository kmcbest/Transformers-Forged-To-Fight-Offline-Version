import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Check CRC32 of transform names
import binascii

def unity_path_hash(path_str):
    # Unity uses CRC32 on the lower-case or exact path string?
    # Actually Unity's AnimationClip genericBindings path is:
    # CRC32 of relative path, or hash of string
    pass

import UnityPy
from pathlib import Path
import subprocess

res = subprocess.check_output(['es.exe', '-n', '5', 'ramjet_gs_deluxe2008.assetbundle'], text=True)
ramjet_path = Path(res.strip().splitlines()[0])
env = UnityPy.load(str(ramjet_path))
obj_map = {o.path_id: o for o in env.objects}

# find Ramjet prop "transformed"
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            props = tt.get("_props", {})
            for k, v in zip(props.get("_serializedKeys", []), props.get("_serializedValues", [])):
                if k == "transformed":
                    print("Ramjet transformed prop:", v)
                    inst_pid = v.get("_instance", {}).get("m_PathID")
                    if inst_pid in obj_map:
                        go = obj_map[inst_pid].read_typetree()
                        print("  Instance GO:", go.get("m_Name"))
