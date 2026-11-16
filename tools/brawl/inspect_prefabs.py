import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

def inspect_prefab(pid, name):
    print(f"\n=== Inspecting {name} (PID={pid}) ===")
    obj = sf.objects.get(pid)
    if not obj:
        print("Object not found!")
        return
    tt = obj.read_typetree()
    print("GameObject Name:", tt.get("m_Name"))
    for comp in tt.get("m_Components", []):
        c_ptr = comp.get("component", {})
        c_pid = c_ptr.get("m_PathID")
        c_obj = sf.objects.get(c_pid)
        c_type = c_obj.type.name if c_obj else "MISSING"
        print(f"  Component: {c_type} (PID={c_pid})")

inspect_prefab(324365576946399764, "brawl_gs.prefab")
inspect_prefab(7253228804562187563, "brawl_gs_lw.prefab")
