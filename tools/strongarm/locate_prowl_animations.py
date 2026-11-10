import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import UnityPy

# 1. Inspect prowl bundle directly
prowl_bp = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
print("=== Inspecting prowl_gs_deluxe2016.assetbundle ===")
env = UnityPy.load(str(prowl_bp))
clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        clips.append((name, obj.path_id))

print(f"Total AnimationClips in prowl bundle: {len(clips)}")
for name, pid in clips:
    print(f"  PID {pid}: {name}")

# 2. Inspect ultramagnus bundle
ultram_bp = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle")
print("\n=== Inspecting ultramagnus_gs_leader.assetbundle ===")
env_u = UnityPy.load(str(ultram_bp))
u_clips = []
for obj in env_u.objects:
    if obj.type.name == "AnimationClip":
        d = obj_read = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        u_clips.append((name, obj.path_id))

print(f"Total AnimationClips in ultramagnus bundle: {len(u_clips)}")
for name, pid in u_clips:
    print(f"  PID {pid}: {name}")

# 3. Where are generic/shared attack animations (e.g. Scout or Car or Deluxe attacks)?
# Let's search extracted_apk for bundles with clips
apk_pack = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack")
candidates = []
for p in apk_pack.rglob("*.assetbundle"):
    pl = p.name.lower()
    if any(k in pl for k in ["archetype", "car", "scout", "tact", "warrior", "brawler", "deluxe", "cin"]):
        candidates.append(p)

print(f"\nScanning {len(candidates)} candidate bundles for attack clips...")
for p in candidates:
    try:
        e = UnityPy.load(str(p))
        found = []
        for obj in e.objects:
            if obj.type.name == "AnimationClip":
                d = obj.read()
                name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
                if any(k in name.lower() for k in ["idle", "light", "heavy", "victory", "win", "special", "levelup"]):
                    found.append(name)
        if found:
            print(f"Bundle {p.name} has {len(found)} relevant clips, e.g. {found[:3]}")
    except Exception:
        pass
