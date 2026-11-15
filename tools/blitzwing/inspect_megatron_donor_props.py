import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path("e:/Agent/TFTF-blender/assets_netflix/megatron_gs_leader2015.assetbundle")
if not donor_path.exists():
    donor_path = Path("e:/Agent/TFTF-blender/assets_base/megatron_gs_leader2015.assetbundle")
if not donor_path.exists():
    # search with Everything
    print("Searching for megatron bundle...")
    import subprocess
    res = subprocess.check_output(['es.exe', '-n', '5', 'megatron_gs_leader2015.assetbundle'], text=True)
    donor_path = Path(res.strip().splitlines()[0])

print(f"Loading Megatron donor from: {donor_path}")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            print(f"\nFound PropsController PID {o.path_id}:")
            props = tt.get("_props", {})
            for k, v in zip(props.get("_serializedKeys", []), props.get("_serializedValues", [])):
                print(f"  Prop '{k}': Name='{v.get('Name')}', InitFlags={v.get('InitFlags')}, Renderers={v.get('_renderers')}")
