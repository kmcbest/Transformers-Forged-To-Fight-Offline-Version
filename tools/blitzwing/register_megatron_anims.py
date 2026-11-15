import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
from copy import copy

root = Path(r"E:\Agent\TFTF-blender")
bp_meg = root / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
bp_proc = root / "assets_netflix" / "character_anim_procedural.assetbundle"
if not bp_proc.exists():
    bp_proc = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\characters_procedural_odr\character_anim_procedural.assetbundle")

out_bp = root / "toolchain" / "megatron_anims_registered.assetbundle"
out_bp.parent.mkdir(parents=True, exist_ok=True)

print("Loading character_anim_procedural.assetbundle...")
env_proc = UnityPy.load(str(bp_proc))

target_clip_names = {
    "brawler_normal_idle",
    "Prefight_Brawler_idle",
    "brawler_normal_attackLight_01_jab",
    "brawler_normal_attackLight_02_jab",
    "brawler_normal_attackLight_03_uppcut",
    "brawler_normal_attackLight_04_frontkick",
    "brawler_normal_attackMedium_01_backhand",
    "brawler_normal_attackMedium_02_shouldercharge",
    "brawler_normal_block",
    "brawler_normal_blockReact",
    "brawler_normal_locoDash_start",
    "brawler_normal_locoDodge",
    "brawler_normal_locoRun",
    "Brawler_Normal_Victory",
    "Brawler_Normal_Victory_Idle",
    "TeamSelect_Brawler_idle"
}

extracted_clips = {}
for obj in env_proc.objects:
    if obj.type.name == "AnimationClip":
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        if name in target_clip_names:
            extracted_clips[name] = (obj.read_typetree(), obj.raw_data)
            print(f"  Extracted procedural: '{name}' (PID={obj.path_id})")

print(f"Extracted {len(extracted_clips)} / {len(target_clip_names)} clips from procedural.")

print("\nLoading Megatron bundle...")
env_meg = UnityPy.load(str(bp_meg))

anim_entries = {}
for obj in env_meg.objects:
    if obj.type.name in ["AnimationClip", "Avatar", "Mesh"]:
        d = obj.read()
        name = getattr(d, 'name', None) or getattr(d, 'm_Name', '')
        if name:
            anim_entries[name] = obj.path_id
            anim_entries[name.lower()] = obj.path_id
            if obj.type.name == "AnimationClip":
                anim_entries[f"assets/anims/{name.lower()}.anim"] = obj.path_id
                anim_entries[f"assets/anims/{name}.anim"] = obj.path_id
            print(f"  Existing Megatron {obj.type.name}: '{name}' (PID={obj.path_id})")

sf = next(f for f in env_meg.file.files.values() if hasattr(f, 'objects'))
max_pid = max(obj.path_id for obj in env_meg.objects)
proto_clip_obj = next(o for o in env_meg.objects if o.type.name == "AnimationClip")

for name, (tree, raw) in extracted_clips.items():
    max_pid += 1
    new_pid = max_pid
    tree["m_Name"] = name
    new_reader = copy(proto_clip_obj)
    new_reader.path_id = new_pid
    new_reader.save_typetree(tree)
    sf.objects[new_pid] = new_reader
    
    anim_entries[name] = new_pid
    anim_entries[f"assets/anims/{name.lower()}.anim"] = new_pid
    anim_entries[f"assets/anims/{name}.anim"] = new_pid
    print(f"  Injected '{name}' as PID={new_pid}")

for obj in env_meg.objects:
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

with open(out_bp, "wb") as f:
    f.write(env_meg.file.save(packer="lz4"))

size_mb = out_bp.stat().st_size / (1024 * 1024)
print(f"\n[✓] Saved registered Megatron animation bundle to:\n  {out_bp} ({size_mb:.2f} MB)")
