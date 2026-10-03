#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_elita_one_bundle.py

Grafts Galactic Trials Elita One onto Arcee's mold:
1. Replaces Arcee's body mesh (cha_arcee_gs_deluxe2014_00) with Elita One's mesh (cha_elita_one_gs_00).
2. Re-routes SMR m_Bones with strict per-prefab physical isolation:
   - Prefab 1 (Showcase: Arcee_GS_Deluxe2014)
   - Prefab 2 (Combat LW: Arcee_GS_Deluxe2014_lw)
3. Transforms Stream 0 coordinates:
   - X_new = px (width)
   - Y_new = pz (height)
   - Z_new = py (depth)
4. Injects exact ground-truth bindposes from Arcee.
5. Updates diffuse, normal, and RAOE textures for main body and vehicle/misc parts.
6. Packages with LZ4 compression.
"""

import copy
import io
import json
import os
import struct
from pathlib import Path
import sys
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

def transform_mesh_stream0(mesh_tree, target_name, bindposes, bone_hashes=None):
    mesh_copy = copy.deepcopy(mesh_tree)
    mesh_copy["m_Name"] = target_name
    mesh_copy["m_BindPose"] = bindposes
    if bone_hashes:
        mesh_copy["m_BoneNameHashes"] = bone_hashes

    vdata = mesh_copy.get('m_VertexData', {})
    v_count = vdata.get('m_VertexCount', 0)
    raw_data = bytearray(vdata.get('m_DataSize', []))
    stride = 40  # stream 0 stride: 12 pos + 12 norm + 16 tan

    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    min_z, max_z = float('inf'), float('-inf')

    for i in range(v_count):
        offset = i * stride
        px, py, pz = struct.unpack_from('<3f', raw_data, offset)
        nx, ny, nz = struct.unpack_from('<3f', raw_data, offset + 12)
        tx, ty, tz, tw = struct.unpack_from('<4f', raw_data, offset + 24)

        # In the new grafted FBX/asset, coordinates are ALREADY Y-up and Z-forward
        new_px, new_py, new_pz = px, py, pz
        new_nx, new_ny, new_nz = nx, ny, nz
        new_tx, new_ty, new_tz = tx, ty, tz

        struct.pack_into('<3f', raw_data, offset, new_px, new_py, new_pz)
        struct.pack_into('<3f', raw_data, offset + 12, new_nx, new_ny, new_nz)
        struct.pack_into('<4f', raw_data, offset + 24, new_tx, new_ty, new_tz, tw)

        min_x = min(min_x, new_px); max_x = max(max_x, new_px)
        min_y = min(min_y, new_py); max_y = max(max_y, new_py)
        min_z = min(min_z, new_pz); max_z = max(max_z, new_pz)

    vdata['m_DataSize'] = bytes(raw_data)
    mesh_copy['m_VertexData'] = vdata

    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    center_z = (min_z + max_z) / 2.0
    extent_x = (max_x - min_x) / 2.0
    extent_y = (max_y - min_y) / 2.0
    extent_z = (max_z - min_z) / 2.0

    mesh_copy['m_LocalAABB'] = {
        'm_Center': {'x': center_x, 'y': center_y, 'z': center_z},
        'm_Extent': {'x': extent_x, 'y': extent_y, 'z': extent_z}
    }
    
    bounds_info = {
        'center_x': center_x, 'center_y': center_y, 'center_z': center_z,
        'extent_x': extent_x, 'extent_y': extent_y, 'extent_z': extent_z,
        'min_x': min_x, 'max_x': max_x,
        'min_y': min_y, 'max_y': max_y,
        'min_z': min_z, 'max_z': max_z
    }
    return mesh_copy, bounds_info

def main():
    root = Path(__file__).resolve().parent.parent.parent
    compiled_bundle_path = root / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
    arcee_bundle_path = root / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
    output_bundle_path = root / "assets_redeco" / "elita_one_gs.assetbundle"
    output_bundle_path.parent.mkdir(parents=True, exist_ok=True)

    if not compiled_bundle_path.is_file():
        raise FileNotFoundError(f"Missing {compiled_bundle_path}. Please build it in Unity first.")

    print(f"[*] Loading compiled Elita One bundle: {compiled_bundle_path.name}...")
    c_env = UnityPy.load(str(compiled_bundle_path))

    print(f"[*] Loading Arcee base bundle: {arcee_bundle_path.name}...")
    i_env = UnityPy.load(str(arcee_bundle_path))

    # 1. Extract Elita One Robot and Vehicle Mesh typetrees
    print("[*] Extracting new SkinnedMeshes from Elita One bundle...")
    robot_mesh_tree = None
    vehicle_mesh_tree = None

    for obj in c_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            m_name = tree.get("m_Name", "")
            if m_name == "cha_elita_one_grafted":
                robot_mesh_tree = tree
                print(f"[+] Found grafted Elita One Robot Mesh: {m_name}, vertices: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
            elif m_name == "cha_elita_one_vehicle_grafted":
                vehicle_mesh_tree = tree
                print(f"[+] Found grafted Elita One Vehicle Mesh: {m_name}, vertices: {tree.get('m_VertexData', {}).get('m_VertexCount')}")

    if robot_mesh_tree is None:
        raise ValueError("Could not find Elita One Robot Mesh in compiled bundle!")
    if vehicle_mesh_tree is None:
        raise ValueError("Could not find Elita One Vehicle Mesh in compiled bundle!")

    # 2. Extract Transform hierarchies for both Prefab 1 and Prefab 2
    tr_to_go = {}
    go_to_tr = {}
    go_dict = {}
    tr_dict = {}

    for obj in i_env.objects:
        if obj.type.name == 'GameObject':
            go_dict[obj.path_id] = obj.read_typetree()
        elif obj.type.name == 'Transform':
            tree = obj.read_typetree()
            tr_dict[obj.path_id] = tree
            go_id = tree.get('m_GameObject', {}).get('m_PathID')
            tr_to_go[obj.path_id] = go_id
            go_to_tr[go_id] = obj.path_id

    def get_prefab_transforms(root_go_id):
        result = {}
        def recurse(go_id):
            go = go_dict.get(go_id)
            if not go: return
            name = go.get('m_Name')
            tr_id = go_to_tr.get(go_id)
            if name not in result:
                result[name] = tr_id
            tr = tr_dict.get(tr_id)
            if tr:
                for child in tr.get('m_Children', []):
                    c_tr_id = child.get('m_PathID')
                    c_go_id = tr_to_go.get(c_tr_id)
                    recurse(c_go_id)
        recurse(root_go_id)
        return result

    # Prefab 1: Arcee_GS_Deluxe2014 (-5193028223035516378)
    # Prefab 2: Arcee_GS_Deluxe2014_lw (-4037407093067927022)
    p1_transforms = get_prefab_transforms(-5193028223035516378)
    p2_transforms = get_prefab_transforms(-4037407093067927022)

    print(f"[+] Prefab 1 (Showcase) has {len(p1_transforms)} transforms.")
    print(f"[+] Prefab 2 (Combat _lw) has {len(p2_transforms)} transforms.")

    # 3. Ground-truth bindposes from Arcee
    arcee_bindposes = None
    arcee_bone_hashes = None
    arcee_smr_bones = []
    arcee_v_bindposes = None
    arcee_v_bone_hashes = None

    for obj in i_env.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_00':
                arcee_bindposes = tree.get('m_BindPose', [])
                arcee_bone_hashes = tree.get('m_BoneNameHashes', [])
            elif tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
                arcee_v_bindposes = tree.get('m_BindPose', [])
                arcee_v_bone_hashes = tree.get('m_BoneNameHashes', [])
        elif obj.type.name == 'SkinnedMeshRenderer':
            tree = obj.read_typetree()
            bones = tree.get('m_Bones', [])
            if len(bones) == 63 and not arcee_smr_bones:
                for b in bones:
                    tr_id = b.get('m_PathID')
                    go_id = tr_to_go.get(tr_id)
                    arcee_smr_bones.append(go_dict.get(go_id, {}).get('m_Name'))

    print(f"[+] Extracted {len(arcee_bindposes)} ground-truth robot bindposes and {len(arcee_smr_bones)} SMR bones from Arcee.")
    print(f"[+] Extracted {len(arcee_v_bindposes)} ground-truth vehicle bindposes from Arcee.")

    target_bindposes = arcee_bindposes

    # CAB remap
    old_cab = "CAB-5eb3be434313f8b01ba027da80ef0a32"
    for obj in i_env.objects:
        if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
            old_cab = obj.assets_file.name
            break
    new_cab = "CAB-elitaonegsdeluxekabam00011223344"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # 4. Transform Robot Mesh (cha_arcee_gs_deluxe2014_00)
    print("[*] Transforming Elita One Robot mesh stream 0...")
    robot_mesh_copy, r_bounds = transform_mesh_stream0(robot_mesh_tree, "cha_arcee_gs_deluxe2014_00", target_bindposes, arcee_bone_hashes)

    # 4.5 Prepare Vehicle Mesh (cha_arcee_gs_deluxe2014_01)
    print("[*] Preparing Elita One Vehicle mesh...")
    vehicle_mesh_copy = copy.deepcopy(vehicle_mesh_tree)
    vehicle_mesh_copy["m_Name"] = "cha_arcee_gs_deluxe2014_01"
    vehicle_mesh_copy["m_BindPose"] = arcee_v_bindposes
    if arcee_v_bone_hashes:
        vehicle_mesh_copy["m_BoneNameHashes"] = arcee_v_bone_hashes
    v_bounds = vehicle_mesh_copy.get("m_LocalAABB", {})

    # 5. Textures
    tex_dir = root / "tools" / "elita_one" / "processed_textures"
    tex_diffuse = tex_dir / "elita_main_diffuse.png"
    tex_normal = tex_dir / "elita_main_normal.png"
    tex_raoe = tex_dir / "elita_main_raoe.png"

    vh_atlas_diff = tex_dir / "elita_veh_atlas_diffuse.png"
    vh_atlas_norm = tex_dir / "elita_veh_atlas_normal.png"
    vh_atlas_raoe = tex_dir / "elita_veh_atlas_raoe.png"

    # 6. Apply replacements
    replaced_robot = False
    replaced_vehicle = False
    routed_smrs = 0

    for obj in i_env.objects:
        if obj.type.name == "Mesh":
            m_tree = obj.read_typetree()
            m_name = m_tree.get("m_Name")
            if m_name == "cha_arcee_gs_deluxe2014_00":
                print(f"[*] Replacing Arcee body mesh with Elita One Robot mesh...")
                replace_str_in_tree(robot_mesh_copy, old_cab, new_cab)
                obj.save_typetree(robot_mesh_copy)
                replaced_robot = True
                print("[✓] Replaced Robot SkinnedMesh successfully!")
            elif m_name == "cha_arcee_gs_deluxe2014_01":
                print(f"[*] Replacing Arcee vehicle mesh with Elita One Vehicle mesh...")
                replace_str_in_tree(vehicle_mesh_copy, old_cab, new_cab)
                obj.save_typetree(vehicle_mesh_copy)
                replaced_vehicle = True
                print("[✓] Replaced Vehicle SkinnedMesh successfully!")
            else:
                replace_str_in_tree(m_tree, old_cab, new_cab)
                obj.save_typetree(m_tree)

        elif obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            
            # Robot SMR (63 bones in base, mapped in Arcee's exact bone order)
            if len(smr.get("m_Bones", [])) == 63:
                is_p1 = (obj.path_id == 8283545308434878436)
                pref_tr = p1_transforms if is_p1 else p2_transforms
                pref_label = "Prefab 1 (Showcase)" if is_p1 else "Prefab 2 (Combat LW)"
                
                new_bones = []
                for bname in arcee_smr_bones:
                    tr_id = pref_tr.get(bname, pref_tr.get("Hips"))
                    new_bones.append({"m_FileID": 0, "m_PathID": tr_id})
                smr["m_Bones"] = new_bones
                smr["m_RootBone"] = {"m_FileID": 0, "m_PathID": pref_tr["Hips"]}
                smr["m_AABB"] = {
                    'm_Center': {'x': r_bounds['center_x'], 'y': r_bounds['center_y'], 'z': r_bounds['center_z']},
                    'm_Extent': {'x': r_bounds['extent_x'], 'y': r_bounds['extent_y'], 'z': r_bounds['extent_z']}
                }
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                routed_smrs += 1
                print(f"[✓] Re-routed Robot SMR in {pref_label} ({len(new_bones)} bones in Arcee order)!")
            elif len(smr.get("m_Bones", [])) == 25:
                # Vehicle SMR
                is_p1 = (obj.path_id == -4178002549372221558)
                pref_label = "Prefab 1 (Showcase)" if is_p1 else "Prefab 2 (Combat LW)"
                if v_bounds:
                    smr["m_AABB"] = copy.deepcopy(v_bounds)
                # Map all 3 submeshes to Material 6920099848281342549 (uses tform_misc_A atlas)
                smr["m_Materials"] = [
                    {"m_FileID": 0, "m_PathID": 6920099848281342549},
                    {"m_FileID": 0, "m_PathID": 6920099848281342549},
                    {"m_FileID": 0, "m_PathID": 6920099848281342549}
                ]
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                print(f"[✓] Re-routed Vehicle SMR in {pref_label} to Elita Vehicle Atlas Material!")
            else:
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)

        elif obj.type.name == "Material":
            mat = obj.read_typetree()
            saved_props = mat.get("m_SavedProperties", {})
            # Tune the 2 main body materials to render bright & opaque
            if obj.path_id in [-737396187749761411, 5182645448333425879]:
                new_floats = []
                for k, v in saved_props.get("m_Floats", []):
                    if k == "_Mode":
                        new_floats.append((k, 0.0))  # Opaque
                    elif k == "_metallic_range":
                        new_floats.append((k, 0.5))  # Metallic
                    elif k == "_roughness_range":
                        new_floats.append((k, 0.6))  # Satin finish
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

                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)
                print(f"[✓] Tuned material {mat.get('m_Name')} for bright vibrant PBR!")

            elif obj.path_id == 6920099848281342549:
                # Vehicle Material
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

                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)
                print(f"[✓] Tuned Vehicle Material for crisp sports car finish!")

            else:
                replace_str_in_tree(mat, old_cab, new_cab)
                obj.save_typetree(mat)

        elif obj.type.name == "Texture2D":
            t_tree = obj.read_typetree()
            t_name = t_tree.get("m_Name", "")
            # Robot Main Textures
            if t_name == "cha_arcee_gs_deluxe2014_main_a" and tex_diffuse.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_diffuse).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Robot Diffuse: {t_name}")
            elif t_name == "main_NM" and tex_normal.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_normal).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Robot Normal: {t_name}")
            elif t_name == "main_tform_misc_RAOE" and tex_raoe.is_file():
                tex = obj.read()
                tex.image = Image.open(tex_raoe).convert("RGB")
                tex.save()
                print(f"[✓] Replaced Robot RAOE: {t_name}")
            # Vehicle Textures (Atlas)
            elif t_name == "tform_misc_A" and vh_atlas_diff.is_file():
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
            else:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)

        elif obj.type.name == "AssetBundle":
            ab = obj.read_typetree()
            container = ab.get("m_Container", [])
            new_container = []
            for item in container:
                first = item[0]
                if isinstance(first, str) and "arcee_gs_deluxe2014" in first:
                    first = first.replace("arcee_gs_deluxe2014", "elita_one_gs")
                if isinstance(item, tuple):
                    new_container.append((first, item[1]))
                elif isinstance(item, list):
                    item[0] = first
                    new_container.append(item)
                else:
                    new_container.append(item)
            ab["m_Container"] = new_container
            replace_str_in_tree(ab, old_cab, new_cab)
            obj.save_typetree(ab)
            print("[✓] Updated AssetBundle container table!")

        else:
            try:
                tree = obj.read_typetree()
                replace_str_in_tree(tree, old_cab, new_cab)
                obj.save_typetree(tree)
            except Exception:
                pass

    print(f"[*] Renaming internal UnityFS CAB entries: {old_cab} -> {new_cab}...")
    bf = list(i_env.files.values())[0]
    new_files = {}
    for subfname, subf in bf.files.items():
        new_subfname = subfname.replace(old_cab, new_cab)
        if hasattr(subf, "name"):
            subf.name = new_subfname
        new_files[new_subfname] = subf
    bf.files = new_files

    print(f"[*] Packaging final AssetBundle with packer='lz4' to {output_bundle_path}...")
    with open(output_bundle_path, "wb") as f:
        f.write(bf.save(packer="lz4"))

    size_mb = output_bundle_path.stat().st_size / (1024 * 1024)
    print(f"\n[✓] SUCCESS: Elita One AssetBundle created: {output_bundle_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
