import UnityPy
from pathlib import Path

def fix_feral_audio():
    src_bundle = Path("extracted_apk/assets/assetpack/characters/character_audio.assetbundle")
    dst_bundle = Path("assets_redeco/character_audio.assetbundle")
    
    print(f"[*] Loading source bundle: {src_bundle}")
    env = UnityPy.load(str(src_bundle))
    obj_map = {obj.path_id: obj for obj in env.objects}
    
    # Target volume and randomization calibrations based on Brawler/Agile baselines
    hit_events = {f"gen_attack_hit_{i}_frl" for i in range(1, 7)}
    swing_events = {f"gen_attack_{i}_frl" for i in range(1, 7)}
    
    modified_count = 0
    
    for obj in env.objects:
        if obj.type.name == "GameObject":
            try:
                tree = obj.read_typetree()
                gname = tree.get("m_Name", "")
                
                # Check if this GameObject is one of our Feral generic events
                if gname in hit_events or gname in swing_events or gname in [
                    "gen_block_frl", "gen_block_react_frl",
                    "gen_hit_react_1_frl", "gen_hit_react_2_frl", "gen_hit_react_3_frl",
                    "gen_damage_1_frl", "gen_damage_2_frl", "gen_damage_3_frl",
                    "gen_dash_frl", "gen_dodge_frl"
                ]:
                    for comp_ref in tree.get("m_Component", []):
                        cpid = comp_ref["component"]["m_PathID"]
                        comp = obj_map.get(cpid)
                        if comp and comp.type.name == "MonoBehaviour":
                            ctree = comp.read_typetree()
                            if "_volume" in ctree:
                                old_vol = ctree["_volume"]
                                
                                if gname in hit_events:
                                    ctree["_volume"] = 1.0000
                                    ctree["_volumeRandomization"] = 0.205671787
                                    ctree["_pitchRandomization"] = 0.122462153
                                elif gname in swing_events:
                                    ctree["_volume"] = 0.6500
                                    ctree["_volumeRandomization"] = 0.205671787
                                    ctree["_pitchRandomization"] = 0.122462153
                                elif gname == "gen_block_frl":
                                    ctree["_volume"] = 1.0000
                                    ctree["_volumeRandomization"] = 0.205671787
                                    ctree["_pitchRandomization"] = 0.122462153
                                elif gname == "gen_block_react_frl":
                                    ctree["_volume"] = 1.0000
                                    ctree["_volumeRandomization"] = 0.1872
                                    ctree["_pitchRandomization"] = 0.0595
                                elif gname.startswith("gen_hit_react_"):
                                    ctree["_volume"] = 0.5012
                                    ctree["_volumeRandomization"] = 0.1087
                                    ctree["_pitchRandomization"] = 0.0595
                                elif gname.startswith("gen_damage_"):
                                    ctree["_volume"] = 0.5012
                                elif gname == "gen_dash_frl":
                                    ctree["_volume"] = 0.6457
                                elif gname == "gen_dodge_frl":
                                    ctree["_volume"] = 0.5000
                                
                                comp.save_typetree(ctree)
                                modified_count += 1
                                print(f"[+] Calibrated {gname:25}: volume {old_vol:.4f} -> {ctree['_volume']:.4f}")
            except Exception as e:
                pass

    print(f"[*] Total modified components: {modified_count}")
    
    # Save with lz4 compression
    dst_bundle.parent.mkdir(parents=True, exist_ok=True)
    dst_bundle.write_bytes(env.file.save(packer="lz4"))
    print(f"[+] Successfully saved calibrated bundle to {dst_bundle} (size: {dst_bundle.stat().st_size} bytes)")

if __name__ == "__main__":
    fix_feral_audio()
