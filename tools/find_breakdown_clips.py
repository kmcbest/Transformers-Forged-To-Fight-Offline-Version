from pathlib import Path
import UnityPy

print("=== Searching for Movie Bumblebee S1 Clip ===")
bb_env = UnityPy.load("extracted_apk/assets/assetpack/bumblebee_cin_dotm_odr/bumblebee_cin_dotm.assetbundle")
for o in bb_env.objects:
    if o.type.name == "AnimationClip":
        name = o.read_typetree().get("m_Name", "")
        if "special_01" in name.lower():
            print(f"Bumblebee cin clip: {name}, path_id={o.path_id}")

print("\n=== Searching for Starscream S2 Clip ===")
# Search procedural bundle, and seeker bundles
bundles = [
    "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle",
    "extracted_apk/assets/assetpack/thundercracker_gs_leader2015_odr/thundercracker_gs_leader2015.assetbundle",
    "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle",
    "extracted_apk/assets/assetpack/ramjet_gs_deluxe2008_odr/ramjet_gs_deluxe2008.assetbundle",
    "extracted_apk/assets/assetpack/dirge_gs_deluxe2008_odr/dirge_gs_deluxe2008.assetbundle",
    "extracted_apk/assets/assetpack/slipstream_gs_odr/slipstream_gs.assetbundle",
]

for b in bundles:
    if Path(b).is_file():
        e = UnityPy.load(b)
        for o in e.objects:
            if o.type.name == "AnimationClip":
                name = o.read_typetree().get("m_Name", "")
                if ("star" in name.lower() or "seeker" in name.lower() or "thund" in name.lower() or "warp" in name.lower()) and "special_02" in name.lower():
                    print(f"Found clip: {name}, path_id={o.path_id} in {Path(b).name}")
