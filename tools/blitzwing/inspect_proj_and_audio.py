import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import UnityPy
from pathlib import Path

ROOT_BL = Path(r"E:\Agent\TFTF-blender")
ROOT_GM = Path(r"E:\Agent\TFTF")

# 1. Inspect projectile_special_bullet in Mixmaster & projectile_sideswipe_missile in Sideswipe
for label, bpath, pname in [
    ("Mixmaster", ROOT_GM / "extracted_apk/assets/assetpack/mixmaster_cin_rotf_odr/mixmaster_cin_rotf.assetbundle", "projectile_special_bullet"),
    ("Sideswipe", ROOT_BL / "extracted_apk/assets/assetpack/sideswipe_gs_odr/sideswipe_gs.assetbundle", "projectile_sideswipe_missile"),
    ("Motormaster", ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle", "projectile_optimus_bullet"),
]:
    env = UnityPy.load(str(bpath))
    omap = {o.path_id: o for o in env.objects}
    print(f"\n=== {label} :: {pname} ===")
    for o in env.objects:
        if o.type.name == "GameObject":
            go = o.read_typetree()
            if go.get("m_Name") == pname:
                for c in go["m_Component"]:
                    cpid = c["component"]["m_PathID"]
                    co = omap[cpid]
                    print(f"  {co.type.name}({cpid}): { {k:v for k,v in co.read_typetree().items() if k != 'm_GameObject'} }")

# 2. Check which FX exist in Megatron's external FileID=3 (effects?) and FileID=9
meg_env = UnityPy.load(str(ROOT_BL / "extracted_apk/assets/assetpack/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle"))
# Also inspect ALL AudioClips in character_audio_procedural matching optimus_prime_gs_projectile_fire
cap = UnityPy.load(str(ROOT_BL / "assets_netflix" / "character_audio_procedural.assetbundle"))
print("\n=== character_audio_procedural optimus_prime_gs_projectile_fire ===")
for o in cap.objects:
    if o.type.name == "AudioClip":
        tt = o.read_typetree()
        if "optimus_prime_gs_projectile_fire" in tt.get("m_Name", ""):
            print(f"  {o.path_id}: {tt['m_Name']} len={tt['m_Length']:.4f} res={tt['m_Resource']}")

# 3. Inspect Megatron CharacterAudio all events
omap = {o.path_id: o for o in meg_env.objects}
ca = omap[-783830211097278398].read_typetree()
print("\n=== Megatron CharacterAudio ALL events ===")
for ev in ca.get("_events", []):
    print(f"  {ev}")

# 4. Inspect projectile moves in moves.assetbundle
moves_env = UnityPy.load(str(ROOT_BL / "assets_netflix" / "moves.assetbundle"))
for o in moves_env.objects:
    if o.type.name == "TextAsset":
        tt = o.read_typetree()
        nm = tt.get("m_Name", "")
        if any(x in nm for x in ("special_bullet", "sideswipe_missile", "optimus_bullet", "mixmaster_special_01")):
            print(f"\n=== MoveText: {nm} PID={o.path_id} ===")
            data = json.loads(tt["m_Script"])
            for ev in data.get("moves", {}).get("events", []):
                t = ev.get("type", "")
                if "Particle" in t or "Audio" in t or "Prop" in t or "Chain" in t or "AttackWindow" in t:
                    print(f"  f={ev.get('f',0)} d={ev.get('d',0)} {t}: { {k:v for k,v in ev.items() if k not in ('cc','sc','mn','dn','id','inf','tar','roc','poc','di')} }")
