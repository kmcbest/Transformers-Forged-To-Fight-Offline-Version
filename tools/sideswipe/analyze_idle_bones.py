import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def analyze_idle_pose(bundle_path, clip_pid, label):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    clip = sf.objects[clip_pid].read_typetree()
    name = clip.get("m_Name")
    print(f"\n=== {label}: {name} (PID {clip_pid}) ===")
    
    # Check MuscleClip / humanoid or generic
    mclip = clip.get("m_MuscleClip", {})
    clip_binding = clip.get("m_ClipBindingConstant", {})
    bindings = clip_binding.get("genericBindings", [])
    print(f"Bindings count: {len(bindings)}")
    
    # Check if humanoid: attribute 1, 2, 3...
    humanoid_attrs = [b for b in bindings if b.get("attribute") in (1, 2, 3, 4)]
    print(f"Humanoid muscle curves count: {len(humanoid_attrs)}")
    if humanoid_attrs:
        print("This is a HUMANOID AnimationClip (uses Mecanim humanoid muscles)!")
    else:
        print("This is a GENERIC AnimationClip (uses bone hierarchy transform curves)!")
        for b in bindings[:10]:
            print(f"  path={b.get('path')}, attr={b.get('attribute')}")

analyze_idle_pose(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle", -2652520226880806548, "Sideswipe current idle")
analyze_idle_pose(ROOT / "extracted_apk" / "assets" / "assetpack" / "necrotronus_gs_kabam_odr" / "necrotronus_gs_kabam.assetbundle", -8455018533602519118, "Necrotronus fight idle")
analyze_idle_pose(ROOT / "extracted_apk" / "assets" / "assetpack" / "megatronus_gs_kabam_odr" / "megatronus_gs_kabam.assetbundle", -341588482639063847, "Megatronus fight idle")
