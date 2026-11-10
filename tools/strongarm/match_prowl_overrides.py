import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# Load procedural clips map
p_proc = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env_proc = UnityPy.load(str(p_proc))
pid_to_name = {}
for obj in env_proc.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        pid_to_name[obj.path_id] = name

print(f"Loaded {len(pid_to_name)} clips from character_anim_procedural.")

# Load Prowl bundle override controller
p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env_prowl = UnityPy.load(str(p_prowl))

for obj in env_prowl.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        print(f"\n--- Overrides in {tree.get('m_Name')} ---")
        clips = tree.get("m_Clips", [])
        for c in clips:
            orig_pid = c.get("m_OriginalClip", {}).get("m_PathID", 0)
            over_pid = c.get("m_OverrideClip", {}).get("m_PathID", 0)
            orig_name = pid_to_name.get(orig_pid, f"Unknown_{orig_pid}")
            over_name = pid_to_name.get(over_pid, f"Unknown_{over_pid}")
            print(f"  {orig_name} -> {over_name}")
