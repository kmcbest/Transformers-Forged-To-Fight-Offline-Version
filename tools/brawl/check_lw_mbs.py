import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, json

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

lw_root = sf.objects.get(7253228804562187563)
tt = lw_root.read_typetree()
for item in tt.get("m_Component", []):
    cpid = item["component"]["m_PathID"]
    cobj = sf.objects.get(cpid)
    if cobj and cobj.type.name == "MonoBehaviour":
        ctt = cobj.read_typetree()
        dump_str = json.dumps(ctt, ensure_ascii=False)
        if "megatron" in dump_str.lower():
            print(f"MonoBehaviour PID {cpid} contains 'megatron'!")
            print(dump_str[:300])
        else:
            print(f"MonoBehaviour PID {cpid} clean (keys: {list(ctt.keys())})")
