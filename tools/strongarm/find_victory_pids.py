import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# Load procedural clips
p_proc = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
env_proc = UnityPy.load(str(p_proc))
pid_to_name = {}
for obj in env_proc.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        pid_to_name[obj.path_id] = getattr(d, 'name', '') or getattr(d, 'm_Name', '')

p_prowl = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env_prowl = UnityPy.load(str(p_prowl))
for obj in env_prowl.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        pid_to_name[obj.path_id] = getattr(d, 'name', '') or getattr(d, 'm_Name', '')

for obj in env_prowl.objects:
    if obj.type.name == "AnimatorOverrideController":
        tree = obj.read_typetree()
        if "fight" in tree.get("m_Name", "").lower():
            print(f"OverrideController: {tree.get('m_Name')}")
            for pair in tree.get("m_Clips", []):
                orig_pid = pair.get("m_OriginalClip", {}).get("m_PathID")
                over_pid = pair.get("m_OverrideClip", {}).get("m_PathID")
                oname = pid_to_name.get(orig_pid, f"Unknown_{orig_pid}")
                vname = pid_to_name.get(over_pid, f"Unknown_{over_pid}")
                if "victory" in oname.lower() or "victory" in vname.lower():
                    print(f"  FOUND: orig_pid={orig_pid} ('{oname}') -> over_pid={over_pid} ('{vname}')")
