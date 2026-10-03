#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graft_vehicle_into_bundle.py

Injects Elita One's vehicle mode into assets_redeco/elita_one_gs.assetbundle:
1. Replaces cha_arcee_gs_deluxe2014_01 with cha_elita_one_vehicle_grafted.
2. Preserves the untouched, working cha_arcee_gs_deluxe2014_00 (Robot Mesh) and SMRs.
3. Sets vehicle SMRs in both Prefab 1 and Prefab 2 to use the Vehicle Atlas Material.
4. Updates vehicle textures (tform_misc_A, tform_misc_NM, wpns_RAOE) with 2048x2048 atlases.
5. Saves with packer="lz4".
"""

import copy
import os
import sys
from pathlib import Path
from PIL import Image

try:
    import UnityPy
except ImportError:
    print("Error: UnityPy is required.")
    sys.exit(1)

sys.stdout.reconfigure(encoding='utf-8')

def replace_str_in_tree(tree_obj, old_s, new_s):
    if isinstance(tree_obj, dict):
        for k, v in tree_obj.items():
            if isinstance(v, str) and old_s in v:
                tree_obj[k] = v.replace(old_s, new_s)
            else:
                replace_str_in_tree(v, old_s, new_s)
    elif isinstance(tree_obj, list):
        for i, item in enumerate(tree_obj):
            if isinstance(item, str) and old_s in item:
                tree_obj[i] = item.replace(old_s, new_s)
            else:
                replace_str_in_tree(item, old_s, new_s)

def main():
    root = Path(__file__).resolve().parent.parent.parent
    mesh_bundle_path = root / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
    target_bundle_path = root / "assets_redeco" / "elita_one_gs.assetbundle"
    arcee_base_path = root / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

    print(f"[*] Loading Unity compiled vehicle mesh: {mesh_bundle_path.name}...")
    c_env = UnityPy.load(str(mesh_bundle_path))
    vehicle_mesh_tree = None
    for obj in c_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            if tree.get("m_Name") == "cha_elita_one_vehicle_grafted":
                vehicle_mesh_tree = tree
                print(f"[✓] Found cha_elita_one_vehicle_grafted: {tree.get('m_VertexData', {}).get('m_VertexCount')} verts")
                break

    if vehicle_mesh_tree is None:
        raise ValueError("Could not find cha_elita_one_vehicle_grafted in mesh bundle!")

    # Load Arcee base bundle to get vehicle bindposes & bone hashes
    base_env = UnityPy.load(str(arcee_base_path))
    arcee_v_bindposes = []
    arcee_v_bone_hashes = []
    for obj in base_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            if tree.get("m_Name") == "cha_arcee_gs_deluxe2014_01":
                arcee_v_bindposes = tree.get("m_BindPose", [])
                arcee_v_bone_hashes = tree.get("m_BoneNameHashes", [])
                break

    # Textures
    tex_dir = root / "tools" / "elita_one" / "processed_textures"
    vh_atlas_diff = tex_dir / "elita_veh_atlas_diffuse.png"
    vh_atlas_norm = tex_dir / "elita_veh_atlas_normal.png"
    vh_atlas_raoe = tex_dir / "elita_veh_atlas_raoe.png"

    # Load target bundle
    print(f"[*] Loading target bundle: {target_bundle_path}...")
    t_env = UnityPy.load(str(target_bundle_path))

    # Identify CAB
    cab_name = "CAB-elitaonegsdeluxekabam00011223344"
    for obj in t_env.objects:
        if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
            cab_name = obj.assets_file.name
            break

    # Prepare replacement vehicle mesh
    v_mesh = copy.deepcopy(vehicle_mesh_tree)
    v_mesh["m_Name"] = "cha_arcee_gs_deluxe2014_01"
    v_mesh["m_BindPose"] = arcee_v_bindposes
    if arcee_v_bone_hashes:
        v_mesh["m_BoneNameHashes"] = arcee_v_bone_hashes
    v_bounds = v_mesh.get("m_LocalAABB", {})
    replace_str_in_tree(v_mesh, "CAB-", cab_name)

    replaced_vehicle = False
    routed_veh_smrs = 0

    for obj in t_env.objects:
        if obj.type.name == "Mesh":
            m_tree = obj.read_typetree()
            if m_tree.get("m_Name") == "cha_arcee_gs_deluxe2014_01":
                print(f"[*] Replacing cha_arcee_gs_deluxe2014_01 with Elita vehicle mesh...")
                obj.save_typetree(v_mesh)
                replaced_vehicle = True
                print("[✓] Successfully replaced vehicle mesh!")

        elif obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            if len(smr.get("m_Bones", [])) == 25:
                # Vehicle SMR
                is_p1 = (obj.path_id == -4178002549372221558)
                label = "Prefab 1 (Showcase)" if is_p1 else "Prefab 2 (Combat LW)"
                if v_bounds:
                    smr["m_AABB"] = copy.deepcopy(v_bounds)
                # Map all submeshes to Material 6920099848281342549 (uses tform_misc_A atlas)
                smr["m_Materials"] = [
                    {"m_FileID": 0, "m_PathID": 6920099848281342549},
                    {"m_FileID": 0, "m_PathID": 6920099848281342549},
                    {"m_FileID": 0, "m_PathID": 6920099848281342549}
                ]
                obj.save_typetree(smr)
                routed_veh_smrs += 1
                print(f"[✓] Re-routed Vehicle SMR in {label} to Elita Vehicle Atlas Material!")

        elif obj.type.name == "Material":
            if obj.path_id == 6920099848281342549:
                mat = obj.read_typetree()
                saved_props = mat.get("m_SavedProperties", {})
                new_floats = []
                for k, v in saved_props.get("m_Floats", []):
                    if k == "_Mode":
                        new_floats.append((k, 0.0))
                    elif k == "_metallic_range":
                        new_floats.append((k, 0.35))
                    elif k == "_roughness_range":
                        new_floats.append((k, 0.55))
                    else:
                        new_floats.append((k, v))
                saved_props["m_Floats"] = new_floats

                new_colors = []
                for k, v in saved_props.get("m_Colors", []):
                    if k in ["_base_col", "_Color", "_base2_col"]:
                        new_colors.append((k, {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}))
                    else:
                        new_colors.append((k, v))
                saved_props["m_Colors"] = new_colors

                # Set _pbr_composite_tex to wpns_RAOE
                new_texs = []
                for k, v in saved_props.get("m_TexEnvs", []):
                    if k == "_pbr_composite_tex":
                        new_texs.append((k, {'m_Texture': {'m_FileID': 0, 'm_PathID': 3139964713313538527}, 'm_Scale': {'x': 1.0, 'y': 1.0}, 'm_Offset': {'x': 0.0, 'y': 0.0}}))
                    else:
                        new_texs.append((k, v))
                saved_props["m_TexEnvs"] = new_texs

                obj.save_typetree(mat)
                print(f"[✓] Tuned Vehicle Material for crisp sports car finish!")

        elif obj.type.name == "Texture2D":
            t_tree = obj.read_typetree()
            t_name = t_tree.get("m_Name", "")
            if t_name == "tform_misc_A" and vh_atlas_diff.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_atlas_diff).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Vehicle Diffuse Atlas: {t_name}")
            elif t_name == "tform_misc_NM" and vh_atlas_norm.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_atlas_norm).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Vehicle Normal Atlas: {t_name}")
            elif t_name == "wpns_RAOE" and vh_atlas_raoe.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_atlas_raoe).convert("RGB")
                tex.save()
                print(f"[✓] Replaced Vehicle RAOE Atlas: {t_name}")

    if not replaced_vehicle:
        raise RuntimeError("Failed to replace vehicle mesh!")

    print(f"[*] Packaging final AssetBundle with packer='lz4'...")
    bf = list(t_env.files.values())[0]
    with open(target_bundle_path, "wb") as f:
        f.write(bf.save(packer="lz4"))

    size_mb = target_bundle_path.stat().st_size / (1024 * 1024)
    print(f"\n[✓] SUCCESS: Elita One AssetBundle updated with Vehicle: {target_bundle_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
