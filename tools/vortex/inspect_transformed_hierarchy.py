import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

gos = {}
transforms = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        gos[obj.path_id] = data
    elif obj.type.name == "Transform":
        data = obj.read_typetree()
        transforms[obj.path_id] = data

def get_go_name(tf_pid):
    tf = transforms.get(tf_pid)
    if not tf:
        return "None"
    go_pid = tf.get("m_GameObject", {}).get("m_PathID")
    go = gos.get(go_pid)
    return go.get("m_Name") if go else f"GO_{go_pid}"

# Find "transformed" GameObjects
for tf_pid, tf in transforms.items():
    go_pid = tf.get("m_GameObject", {}).get("m_PathID")
    go = gos.get(go_pid)
    if go and go.get("m_Name") == "transformed":
        print(f"\nFound 'transformed' GameObject (PID {go_pid}, Transform {tf_pid}):")
        # Print children recursively
        def print_tree(curr_tf_pid, depth=0):
            indent = "  " * depth
            curr_tf = transforms.get(curr_tf_pid)
            if not curr_tf: return
            c_go_pid = curr_tf.get("m_GameObject", {}).get("m_PathID")
            c_go = gos.get(c_go_pid)
            c_name = c_go.get("m_Name") if c_go else "unknown"
            
            # Check what components on c_go
            comps = []
            if c_go:
                for c in c_go.get("m_Component", []):
                    c_id = c.get("component", {}).get("m_PathID")
                    # find component type
                    pass
            print(f"{indent}- {c_name} (TF: {curr_tf_pid}, GO: {c_go_pid})")
            for ch in curr_tf.get("m_Children", []):
                print_tree(ch.get("m_PathID"), depth + 1)
        
        print_tree(tf_pid)
