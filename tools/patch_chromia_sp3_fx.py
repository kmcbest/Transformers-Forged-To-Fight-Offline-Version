"""
Patch Chromia SP3 VFX:
1. Make particle meshes (SlashMesh5, fx_msh_wind_spin, fx_msh_wind_spin_small) readable in assets_redeco/character_fx_procedural.assetbundle
2. Port 4 particle materials (axe trail and wind rings) in chromia_gs_kabam.assetbundle to compatible Unity 2018/2020 format
   with compatible shader references to character_fx.assetbundle.
"""
from pathlib import Path
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
REDECO_DIR = ROOT / "assets_redeco"
NETFLIX_DIR = ROOT / "assets_netflix"
EXTRACTED_DIR = ROOT / "extracted_apk"


def patch_procedural_fx():
    print(">>> [1/2] Patching assets_redeco/character_fx_procedural.assetbundle...")
    bundle_path = REDECO_DIR / "character_fx_procedural.assetbundle"
    assert bundle_path.exists(), f"Missing {bundle_path}"
    
    env = UnityPy.load(bundle_path.read_bytes())
    sf = list(env.file.files.values())[0]
    
    target_mesh_pids = {
        4547667473076947885: "SlashMesh5",
        5070877881822408183: "fx_msh_wind_spin",
        -8468514086234420794: "fx_msh_wind_spin_small"
    }
    
    for pid, mname in target_mesh_pids.items():
        assert pid in sf.objects, f"Mesh {mname} (PID={pid}) not found in procedural fx bundle!"
        obj = sf.objects[pid]
        tree = obj.read_typetree()
        print(f"  - Mesh {tree.get('m_Name')} (PID={pid}): setting m_IsReadable = True")
        tree["m_IsReadable"] = True
        obj.save_typetree(tree)
        
    saved_bytes = env.file.save(packer="lz4")
    bundle_path.write_bytes(saved_bytes)
    print(f"  [+] Saved {bundle_path} ({len(saved_bytes)} bytes)")
    
    # Verify
    verify_env = UnityPy.load(bundle_path.read_bytes())
    vsf = list(verify_env.file.files.values())[0]
    for pid, mname in target_mesh_pids.items():
        vtree = vsf.objects[pid].read_typetree()
        assert vtree.get("m_IsReadable") is True, f"Failed to verify m_IsReadable for {mname}!"
    print("  [+] Verified all 3 meshes have m_IsReadable = True.")


def patch_chromia_bundle():
    print("\n>>> [2/2] Patching chromia_gs_kabam.assetbundle materials...")
    base_fx_path = EXTRACTED_DIR / "assets" / "assetpack" / "characters" / "character_fx.assetbundle"
    assert base_fx_path.exists(), f"Missing {base_fx_path}"
    
    # 1. Extract compatible Material SerializedType from base character_fx.assetbundle
    env_fx = UnityPy.load(base_fx_path.read_bytes())
    sf_fx = list(env_fx.file.files.values())[0]
    compat_mat_type = next(t for t in sf_fx.types if t.class_id == 21)
    
    # 2. Load Chromia bundle from assets_netflix
    source_chromia_path = NETFLIX_DIR / "chromia_gs_kabam.assetbundle"
    assert source_chromia_path.exists(), f"Missing {source_chromia_path}"
    
    env_ch = UnityPy.load(source_chromia_path.read_bytes())
    sf_ch = list(env_ch.file.files.values())[0]
    
    # Append compatible Material type
    sf_ch.types.append(compat_mat_type)
    compat_type_index = len(sf_ch.types) - 1
    print(f"  - Appended compatible Material type at index {compat_type_index}")
    
    target_materials = {
        -7031090236892197484: ("fx_m_Chromia_SP3_trail_always", 1, -6819097818903621761), # EB/Particle/PBR/Base in character_fx (FileID 1)
        -6280747740330191934: ("fx_m_Chromia_SP3_trail_PoleSwing", 1, -6819097818903621761), # EB/Particle/PBR/Base in character_fx (FileID 1)
        -333760790010993664: ("fx_m_chromia_pink_spine_smoke_b", 2, -5794361538478127441), # EB/Particle/LowRes/PBR/Blend in character_fx_procedural (FileID 2)
        7800166128171342672: ("fx_m_chromia_blue_spine_smoke_b", 2, -5794361538478127441), # EB/Particle/LowRes/PBR/Blend in character_fx_procedural (FileID 2)
    }
    
    for pid, (mname, file_id, shader_pid) in target_materials.items():
        assert pid in sf_ch.objects, f"Material {mname} (PID={pid}) not found!"
        obj = sf_ch.objects[pid]
        tree = obj.read_typetree()
        
        # Update shader reference to external FileID (1: character_fx, 2: character_fx_procedural)
        tree["m_Shader"] = {"m_FileID": file_id, "m_PathID": shader_pid}
        
        # Convert keywords
        keywords = tree.get("m_ValidKeywords", [])
        if isinstance(keywords, list):
            tree["m_ShaderKeywords"] = " ".join(keywords)
        else:
            tree["m_ShaderKeywords"] = str(keywords) if keywords else ""
            
        tree.pop("m_ValidKeywords", None)
        tree.pop("m_InvalidKeywords", None)
        
        obj.type_id = compat_type_index
        obj.serialized_type = compat_mat_type
        obj.save_typetree(tree, nodes=compat_mat_type.node)
        print(f"  - Converted material {mname} -> FileID {file_id}, shader PID {shader_pid}, keywords: {tree['m_ShaderKeywords']!r}")

    # Ensure S3 axe SkinnedMeshRenderer material points to valid 1952278396157663915
    for obj in sf_ch.objects.values():
        if obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            if tree.get("m_Materials") == [{"m_FileID": 0, "m_PathID": 5363102012143072554}]:
                tree["m_Materials"] = [{"m_FileID": 0, "m_PathID": 1952278396157663915}]
                obj.save_typetree(tree)
        
    saved_bytes = env_ch.file.save(packer="lz4")
    target_path = REDECO_DIR / "chromia_gs_kabam.assetbundle"
    target_path.write_bytes(saved_bytes)
    print(f"  [+] Saved {target_path} ({len(saved_bytes)} bytes)")
    
    # 3. Verification of saved bundle
    verify_env = UnityPy.load(target_path.read_bytes())
    vsf = list(verify_env.file.files.values())[0]
    for pid, (mname, file_id, shader_pid) in target_materials.items():
        vobj = vsf.objects[pid]
        vtree = vobj.read_typetree()
        assert vtree.get("m_Shader", {}).get("m_FileID") == file_id
        assert vtree.get("m_Shader", {}).get("m_PathID") == shader_pid
        assert bool(vtree.get("m_ShaderKeywords")), f"Missing shader keywords on {mname}!"
        assert vtree.get("m_ValidKeywords") is None
    print("  [+] Verified all 4 materials in output bundle.")


def patch_deadend_bundle():
    print("\n>>> [3/4] Patching deadend_gs_deluxe2015.assetbundle materials & prefabs...")
    base_fx_path = EXTRACTED_DIR / "assets" / "assetpack" / "characters" / "character_fx.assetbundle"
    assert base_fx_path.exists(), f"Missing {base_fx_path}"

    # 1. Extract compatible Material SerializedType from base character_fx.assetbundle
    env_fx = UnityPy.load(base_fx_path.read_bytes())
    sf_fx = list(env_fx.file.files.values())[0]
    compat_mat_type = next(t for t in sf_fx.types if t.class_id == 21)

    # 2. Load Dead End bundle from assets_netflix
    source_deadend_path = NETFLIX_DIR / "deadend_gs_deluxe2015.assetbundle"
    assert source_deadend_path.exists(), f"Missing {source_deadend_path}"

    env_de = UnityPy.load(source_deadend_path.read_bytes())
    sf_de = list(env_de.file.files.values())[0]

    # Append compatible Material type
    sf_de.types.append(compat_mat_type)
    compat_type_index = len(sf_de.types) - 1
    print(f"  - Appended compatible Material type at index {compat_type_index}")

    # Dead End externals:
    # FileID 1: CAB-7b4e... (character_fx_procedural.assetbundle) -> has EB/Particle/PBR/Base (-6819097818903621761) and EB/Particle/LowRes/PBR/Blend (-5794361538478127441)
    target_materials = {
        95094745365683190: ("fx_m_DeadEnd_SP3_trail_matinee", 1, -6819097818903621761),
        9105687319178105237: ("fx_m_DeadEnd_SP3_trail_PoleSwing_matinne", 1, -6819097818903621761),
        -5967951594327103068: ("fx_m_deadend_pink_spine_smoke_b", 1, -5794361538478127441),
        -303334430202936358: ("fx_m_deadend_blue_spine_smoke_b", 1, -5794361538478127441),
    }

    for pid, (mname, file_id, shader_pid) in target_materials.items():
        assert pid in sf_de.objects, f"Material {mname} (PID={pid}) not found!"
        obj = sf_de.objects[pid]
        tree = obj.read_typetree()

        # Update shader reference to external FileID (1: character_fx_procedural)
        tree["m_Shader"] = {"m_FileID": file_id, "m_PathID": shader_pid}

        # Convert keywords
        keywords = tree.get("m_ValidKeywords", [])
        if isinstance(keywords, list):
            tree["m_ShaderKeywords"] = " ".join(keywords)
        else:
            tree["m_ShaderKeywords"] = str(keywords) if keywords else ""

        tree.pop("m_ValidKeywords", None)
        tree.pop("m_InvalidKeywords", None)

        obj.type_id = compat_type_index
        obj.serialized_type = compat_mat_type
        obj.save_typetree(tree, nodes=compat_mat_type.node)
        print(f"  - Converted material {mname} -> FileID {file_id}, shader PID {shader_pid}, keywords: {tree['m_ShaderKeywords']!r}")

    # 3. Ensure weapon SkinnedMeshRenderer materials point to valid 8990873932192355227
    weapon_mats_patched = 0
    for obj in sf_de.objects.values():
        if obj.type.name == "SkinnedMeshRenderer":
            tree = obj.read_typetree()
            mats = tree.get("m_Materials", [])
            modified = False
            for m in mats:
                if m.get("m_PathID") in [5840752304272669847, -8150449380963715650]:
                    m["m_FileID"] = 0
                    m["m_PathID"] = 8990873932192355227
                    modified = True
            if modified:
                obj.save_typetree(tree)
                weapon_mats_patched += 1
    print(f"  - Verified/patched {weapon_mats_patched} weapon SkinnedMeshRenderers to valid material 8990873932192355227")

    # 4. Fix grenade projectile PrefabList: map missing fx_p_dagger_streaks_kickback (-4095703740051711630) to base fx_p_dagger_streaks (-8238248468515280584)
    if -4118918894999562532 in sf_de.objects:
        p_obj = sf_de.objects[-4118918894999562532]
        p_tree = p_obj.read_typetree()
        plist = p_tree.get("PrefabList", [])
        for entry in plist:
            prefab = entry.get("Prefab", {})
            if prefab.get("m_PathID") == -4095703740051711630:
                prefab["m_FileID"] = 1
                prefab["m_PathID"] = -8238248468515280584
                print("  - Remapped grenade projectile streak prefab to base fx_p_dagger_streaks (-8238248468515280584)")
        p_obj.save_typetree(p_tree)

    # 5. Fix AssetBundle preload table: remap -4095703740051711630 to -8238248468515280584
    for obj in sf_de.objects.values():
        if obj.type.name == "AssetBundle":
            ab_tree = obj.read_typetree()
            preload = ab_tree.get("m_PreloadTable", [])
            modified_preload = False
            for item in preload:
                if item.get("m_PathID") == -4095703740051711630:
                    item["m_FileID"] = 1
                    item["m_PathID"] = -8238248468515280584
                    modified_preload = True
            if modified_preload:
                obj.save_typetree(ab_tree)
                print("  - Remapped -4095703740051711630 to -8238248468515280584 in AssetBundle preload table")

    saved_bytes = env_de.file.save(packer="lz4")
    target_path = REDECO_DIR / "deadend_gs_deluxe2015.assetbundle"
    target_path.write_bytes(saved_bytes)
    print(f"  [+] Saved {target_path} ({len(saved_bytes)} bytes)")

    # 5. Verification of saved bundle
    verify_env = UnityPy.load(target_path.read_bytes())
    vsf = list(verify_env.file.files.values())[0]
    for pid, (mname, file_id, shader_pid) in target_materials.items():
        vobj = vsf.objects[pid]
        vtree = vobj.read_typetree()
        assert vtree.get("m_Shader", {}).get("m_FileID") == file_id
        assert vtree.get("m_Shader", {}).get("m_PathID") == shader_pid
        assert bool(vtree.get("m_ShaderKeywords")), f"Missing shader keywords on {mname}!"
        assert vtree.get("m_ValidKeywords") is None
    print("  [+] Verified all 4 Dead End materials in output bundle.")


def patch_moves_bundle():
    print("\n>>> [4/4] Checking and patching assets_redeco/moves.assetbundle...")
    moves_path = REDECO_DIR / "moves.assetbundle"
    assert moves_path.exists(), f"Missing {moves_path}"

    env = UnityPy.load(moves_path.read_bytes())
    moves_count = 0
    modified = False

    for obj in env.objects:
        if obj.type.name == "TextAsset":
            tree = obj.read_typetree()
            name = tree.get("m_Name", "")
            if name.startswith("move_"):
                moves_count += 1
            script = tree.get("m_Script", "")
            if "fx_p_dagger_streaks_kickback" in script:
                tree["m_Script"] = script.replace("fx_p_dagger_streaks_kickback", "fx_p_dagger_streaks")
                obj.save_typetree(tree)
                modified = True
                print(f"  - Replaced fx_p_dagger_streaks_kickback in {name}")

    print(f"  - Verified total moves count: {moves_count}")
    assert moves_count >= 945, f"CRITICAL: moves_count ({moves_count}) < 945!"

    if modified:
        saved_bytes = env.file.save(packer="lz4")
        moves_path.write_bytes(saved_bytes)
        print(f"  [+] Saved patched {moves_path} ({len(saved_bytes)} bytes)")
    else:
        print("  - moves.assetbundle already clean.")


if __name__ == "__main__":
    patch_procedural_fx()
    patch_chromia_bundle()
    patch_deadend_bundle()
    patch_moves_bundle()
    print("\n🎉 Chromia & Dead End VFX asset bundles successfully patched and verified!")
