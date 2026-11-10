import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

root = Path(r"E:\Agent\TFTF-blender")
bp_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
bp_proc = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")
out_bp = root / "toolchain" / "prowl_anims_registered.assetbundle"
out_bp.parent.mkdir(parents=True, exist_ok=True)

print("Loading character_anim_procedural.assetbundle...")
env_proc = UnityPy.load(str(bp_proc))

# Desired clips to extract from procedural bundle
target_clip_names = {
    "tactical_normal_idle",
    "Prefight_Tactical_idle",
    "tactical_normal_attacklight_01_jab_L",
    "tactical_normal_attacklight_02_jab_R",
    "tactical_normal_attacklight_03_hook_L",
    "tactical_normal_attacklight_04_uppercut_R",
    "tactical_normal_attackMedium_01_elbow_L_01",
    "tactical_normal_attackMedium_02_kick_R",
    "Car_Normal_attackHeavy",
    "Prowl_Normal_attackSpecial_01",
    "Prowl_Normal_attackSpecial_02",
    "Prowl_Normal_attackSpecial_02_shotgun_Prop",
    "prowl_gs_delux_attackSpecial_03",
    "prowl_gs_delux_attackSpecial_03_Chain_Prop",
    "prowl_gs_delux_attackSpecial_03_hitReaction",
    "Ultramagnus_Normal_victory",
    "Ultramagnus_Normal_victory_idle",
}

extracted_clips = {}
for obj in env_proc.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        if name in target_clip_names:
            extracted_clips[name] = (obj.read_typetree(), obj.raw_data)
            print(f"  Extracted '{name}' (PID={obj.path_id})")

print(f"Extracted {len(extracted_clips)} / {len(target_clip_names)} target clips from procedural.")

print("\nLoading Prowl bundle...")
env_prowl = UnityPy.load(str(bp_prowl))

# Collect existing clips in Prowl bundle
anim_entries = {}
for obj in env_prowl.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        anim_entries[name] = obj.path_id
        anim_entries[f"assets/anims/{name.lower()}.anim"] = obj.path_id
        anim_entries[f"assets/anims/{name}.anim"] = obj.path_id
        print(f"  Existing Prowl clip: '{name}'")

# Inject extracted clips into Prowl bundle serialized file
# Find the main SerializedFile
sf = next(f for f in env_prowl.file.files.values() if hasattr(f, 'objects'))

# Allocate new PathIDs for injected clips
max_pid = max(obj.path_id for obj in env_prowl.objects)
for name, (tree, raw) in extracted_clips.items():
    max_pid += 1
    new_pid = max_pid
    # Set path_id in tree
    tree["m_Name"] = name
    
    # We can inject into sf using UnityPy's save_typetree or add object
    # In UnityPy, sf.objects is a dict: path_id -> ObjectReader
    # Let's clone an existing AnimationClip object reader or save typetree
    # An easier way: create a dummy object reader or use typetree injection
    # Let's find an existing AnimationClip in sf
    proto_clip_obj = next(o for o in env_prowl.objects if o.type.name == "AnimationClip")
    # Clone reader
    from copy import copy
    new_reader = copy(proto_clip_obj)
    new_reader.path_id = new_pid
    new_reader.save_typetree(tree)
    sf.objects[new_pid] = new_reader
    
    anim_entries[name] = new_pid
    anim_entries[f"assets/anims/{name.lower()}.anim"] = new_pid
    anim_entries[f"assets/anims/{name}.anim"] = new_pid
    print(f"  Injected '{name}' as PID={new_pid}")

# Update AssetBundle m_Container
for obj in env_prowl.objects:
    if obj.type.name == "AssetBundle":
        tree = obj.read_typetree()
        c = tree.get("m_Container", [])
        existing_keys = {item[0] for item in c}
        for name, pid in anim_entries.items():
            if name not in existing_keys:
                entry = (name, {'preloadIndex': 0, 'preloadSize': 0, 'asset': {'m_FileID': 0, 'm_PathID': pid}})
                c.append(entry)
        tree["m_Container"] = c
        obj.save_typetree(tree)
        print("\nUpdated AssetBundle.m_Container with all AnimationClips!")

# Save to toolchain/prowl_anims_registered.assetbundle
with open(out_bp, "wb") as f:
    f.write(env_prowl.file.save(packer="lz4"))

size_mb = out_bp.stat().st_size / (1024 * 1024)
print(f"\n[✓] Saved registered Prowl animation bundle to:\n  {out_bp} ({size_mb:.2f} MB)")
