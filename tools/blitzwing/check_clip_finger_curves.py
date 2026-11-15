import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle")
env = UnityPy.load(str(BUNDLE_PATH))

print(f"Loaded {len(env.objects)} objects from registered bundle")
anims = [o for o in env.objects if o.type.name == "AnimationClip"]
print(f"Found {len(anims)} AnimationClips")

# Check first 3 clips for finger curves
for obj in anims[:5]:
    tree = obj.read_typetree()
    cname = tree.get("m_Name", "Unknown")
    print(f"\nClip: '{cname}'")
    
    # Check animated bone paths
    rot_curves = tree.get("m_RotationCurves", [])
    float_curves = tree.get("m_FloatCurves", [])
    pptr_curves = tree.get("m_PPtrCurves", [])
    
    bone_paths = set()
    for rc in rot_curves:
        bone_paths.add(rc.get("path"))
        
    finger_paths = [p for p in bone_paths if any(k in p for k in ["Thumb", "Index", "Middle", "Ring", "Pinky"])]
    print(f"  Total animated rot paths: {len(bone_paths)}, finger paths: {len(finger_paths)}")
    for fp in finger_paths[:6]:
        print(f"    {fp}")
