import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle")
env = UnityPy.load(str(BUNDLE_PATH))

# Let's inspect all animation clips to see if ANY clip has Transform rotation curves
found_any_curves = False
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        cname = tree.get("m_Name", "")
        rot_curves = tree.get("m_RotationCurves", [])
        eul_curves = tree.get("m_EulerCurves", [])
        if rot_curves or eul_curves:
            print(f"Clip '{cname}' has {len(rot_curves)} rot curves, {len(eul_curves)} euler curves")
            found_any_curves = True
            for rc in rot_curves:
                p = rc.get("path", "")
                if "Thumb" in p or "Index" in p:
                    print(f"   path: {p}")

if not found_any_curves:
    print("None of the clips have m_RotationCurves or m_EulerCurves (all use Mecanim Muscle Clips).")
