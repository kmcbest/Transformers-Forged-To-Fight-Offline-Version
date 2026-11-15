import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            print(f"PropsController PID={o.path_id}:")
            print("  Keys:", tt["_props"]["_serializedKeys"])
            for p in tt["_props"]["_serializedValues"]:
                if p["Name"] in ("transformed", "cannon"):
                    print(f"    Prop '{p['Name']}': InitFlags={p['InitFlags']}, Renderers={p['_renderers']}")
