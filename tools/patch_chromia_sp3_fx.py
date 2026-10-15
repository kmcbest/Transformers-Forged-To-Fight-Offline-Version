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
        -7031090236892197484: ("fx_m_Chromia_SP3_trail_always", -6819097818903621761), # EB/Particle/PBR/Base
        -6280747740330191934: ("fx_m_Chromia_SP3_trail_PoleSwing", -6819097818903621761), # EB/Particle/PBR/Base
        -333760790010993664: ("fx_m_chromia_pink_spine_smoke_b", -5794361538478127441), # EB/Particle/LowRes/PBR/Blend
        7800166128171342672: ("fx_m_chromia_blue_spine_smoke_b", -5794361538478127441), # EB/Particle/LowRes/PBR/Blend
    }
    
    for pid, (mname, shader_pid) in target_materials.items():
        assert pid in sf_ch.objects, f"Material {mname} (PID={pid}) not found!"
        obj = sf_ch.objects[pid]
        tree = obj.read_typetree()
        
        # Update shader reference to external FileID 1 (character_fx.assetbundle)
        tree["m_Shader"] = {"m_FileID": 1, "m_PathID": shader_pid}
        
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
        print(f"  - Converted material {mname} -> shader PID {shader_pid}, keywords: {tree['m_ShaderKeywords']!r}")
        
    saved_bytes = env_ch.file.save(packer="lz4")
    target_path = REDECO_DIR / "chromia_gs_kabam.assetbundle"
    target_path.write_bytes(saved_bytes)
    print(f"  [+] Saved {target_path} ({len(saved_bytes)} bytes)")
    
    # 3. Verification of saved bundle
    verify_env = UnityPy.load(target_path.read_bytes())
    vsf = list(verify_env.file.files.values())[0]
    for pid, (mname, shader_pid) in target_materials.items():
        vobj = vsf.objects[pid]
        vtree = vobj.read_typetree()
        assert vtree.get("m_Shader", {}).get("m_FileID") == 1
        assert vtree.get("m_Shader", {}).get("m_PathID") == shader_pid
        assert bool(vtree.get("m_ShaderKeywords")), f"Missing shader keywords on {mname}!"
        assert vtree.get("m_ValidKeywords") is None
    print("  [+] Verified all 4 materials in output bundle.")


if __name__ == "__main__":
    patch_procedural_fx()
    patch_chromia_bundle()
    print("\n🎉 Chromia SP3 VFX asset bundles successfully patched!")
