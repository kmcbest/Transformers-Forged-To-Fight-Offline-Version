import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"

env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

# List all GameObjects under Stage
STAGE_ROOT = 3256447252977910551

# Let's traverse Transforms from STAGE_ROOT
root_go = sf.objects[STAGE_ROOT]
print(f"Root GO: {root_go.read_typetree().get('m_Name')}")

# Find its Transform
def print_tree(go_pid, indent=0):
    go = sf.objects.get(go_pid)
    if not go: return
    gtt = go.read_typetree()
    gname = gtt.get('m_Name')
    # Find components
    comp_types = []
    tr_pid = None
    for c in gtt.get('m_Component', []):
        c_pid = c.get('component', {}).get('m_PathID')
        c_obj = sf.objects.get(c_pid)
        if c_obj:
            comp_types.append(c_obj.type.name)
            if c_obj.type.name in ('Transform', 'RectTransform'):
                tr_pid = c_pid
    print("  " * indent + f"{gname} (GO {go_pid}, {comp_types})")
    if tr_pid:
        tr_tt = sf.objects[tr_pid].read_typetree()
        for child in tr_tt.get('m_Children', []):
            ch_tr_pid = child.get('m_PathID')
            ch_tr = sf.objects.get(ch_tr_pid)
            if ch_tr:
                ch_go_pid = ch_tr.read_typetree().get('m_GameObject', {}).get('m_PathID')
                if ch_go_pid:
                    print_tree(ch_go_pid, indent + 1)

print_tree(STAGE_ROOT)
