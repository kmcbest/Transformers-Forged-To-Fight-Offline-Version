#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_demolishor_bundle.py

Grafts BOTH Demolishor humanoid robot and vehicle (tank) into Ironhide's AssetBundle:
1. Replaces Ironhide's body mesh (cha_ironhide_cin_rotf_00) with Demolishor's robot mesh (cha_demolishor_gs_00).
2. Replaces Ironhide's vehicle mesh (cha_ironhide_cin_rotf_01) with Demolishor's tank mesh (cha_demolishor_gs_01).
3. Re-routes SMR m_Bones with strict per-prefab physical isolation:
   - Prefab 1 (Showcase: ironhide_cin_rotf.prefab)
   - Prefab 2 (Combat LW: ironhide_cin_rotf_lw.prefab)
4. Transforms Stream 0 coordinates:
   - X_new = px (width)
   - Y_new = pz (height)
   - Z_new = -py (depth)
5. Injects exact ground-truth bindposes from Ironhide.
6. Updates robot and vehicle diffuse, normal, and RAOE textures.
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

def transform_mesh_stream0(mesh_tree, target_name, bindposes):
    mesh_copy = copy.deepcopy(mesh_tree)
    mesh_copy["m_Name"] = target_name
    mesh_copy["m_BindPose"] = bindposes

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

        # X_new = px, Y_new = pz, Z_new = -py
        new_px, new_py, new_pz = px, pz, -py
        new_nx, new_ny, new_nz = nx, nz, -ny
        new_tx, new_ty, new_tz = tx, tz, -ty

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
    compiled_bundle_path = root / "toolchain" / "unity_build_project" / "AssetBundles" / "demolishor_mesh.assetbundle"
    ironhide_bundle_path = root / "extracted_apk" / "assets" / "assetpack" / "ironhide_cin_rotf_odr" / "ironhide_cin_rotf.assetbundle"
    output_bundle_path = root / "assets_redeco" / "demolishor_gs.assetbundle"
    output_bundle_path.parent.mkdir(parents=True, exist_ok=True)

    if not compiled_bundle_path.is_file():
        raise FileNotFoundError(f"Missing {compiled_bundle_path}. Please build it in Unity first.")

    print(f"[*] Loading compiled Demolishor bundle: {compiled_bundle_path.name}...")
    c_env = UnityPy.load(str(compiled_bundle_path))

    print(f"[*] Loading Ironhide base bundle: {ironhide_bundle_path.name}...")
    i_env = UnityPy.load(str(ironhide_bundle_path))

    # 1. Extract Demolishor Robot & Vehicle Mesh typetrees
    print("[*] Extracting new SkinnedMeshes from Demolishor bundle...")
    robot_mesh_tree = None
    vh_mesh_tree = None

    d_path_to_name = {}
    for obj in c_env.objects:
        if obj.type.name == "Transform":
            t = obj.read_typetree()
            go_ptr = t.get("m_GameObject", {})
            for g_obj in c_env.objects:
                if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                    d_path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                    break

    robot_bone_names = []
    vh_bone_names = []

    for obj in c_env.objects:
        if obj.type.name == "Mesh":
            tree = obj.read_typetree()
            m_name = tree.get("m_Name", "").lower()
            if "01" in m_name or "vh" in m_name:
                vh_mesh_tree = tree
                print(f"[+] Found Demolishor Vehicle Mesh: {tree.get('m_Name')}, vertices: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
            elif "demolishor" in m_name:
                robot_mesh_tree = tree
                print(f"[+] Found Demolishor Robot Mesh: {tree.get('m_Name')}, vertices: {tree.get('m_VertexData', {}).get('m_VertexCount')}")
        elif obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            mesh_pid = smr.get("m_Mesh", {}).get("m_PathID")
            # Determine if this SMR belongs to robot or vehicle
            bones = [d_path_to_name.get(b.get("m_PathID")) for b in smr.get("m_Bones", [])]
            if len(bones) == 80:
                robot_bone_names = bones
            elif len(bones) == 47:
                vh_bone_names = bones

    if robot_mesh_tree is None:
        raise ValueError("Could not find Demolishor Robot Mesh in compiled bundle!")

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

    p1_transforms = get_prefab_transforms(8887288183430146843)
    p2_transforms = get_prefab_transforms(-4129943903446534184)
    print(f"[+] Prefab 1 (Showcase) has {len(p1_transforms)} transforms.")
    print(f"[+] Prefab 2 (Combat _lw) has {len(p2_transforms)} transforms.")

    # 3. Ground-truth bindposes from Ironhide
    iron_bindposes = None
    iron_smr_bones = []
    iron_vh_bindposes = None
    iron_vh_bones = []

    for obj in i_env.objects:
        if obj.type.name == 'Mesh':
            tree = obj.read_typetree()
            if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
                iron_bindposes = tree.get('m_BindPose', [])
            elif tree.get('m_Name') == 'cha_ironhide_cin_rotf_01':
                iron_vh_bindposes = tree.get('m_BindPose', [])
        elif obj.type.name == 'SkinnedMeshRenderer':
            tree = obj.read_typetree()
            bones = tree.get('m_Bones', [])
            if len(bones) == 80 and not iron_smr_bones:
                for b in bones:
                    tr_id = b.get('m_PathID')
                    go_id = tr_to_go.get(tr_id)
                    iron_smr_bones.append(go_dict.get(go_id, {}).get('m_Name'))
            elif len(bones) == 47 and not iron_vh_bones:
                for b in bones:
                    tr_id = b.get('m_PathID')
                    go_id = tr_to_go.get(tr_id)
                    iron_vh_bones.append(go_dict.get(go_id, {}).get('m_Name'))

    # Reorder robot bindposes
    if not robot_bone_names:
        robot_bone_names = iron_smr_bones
    reordered_robot_bindposes = []
    for bname in robot_bone_names:
        idx = iron_smr_bones.index(bname) if bname in iron_smr_bones else 0
        reordered_robot_bindposes.append(copy.deepcopy(iron_bindposes[idx]))

    # CAB remap
    old_cab = "CAB-27c22a4e1ba6ebaa32da31397ad32207"
    for obj in i_env.objects:
        if hasattr(obj, "assets_file") and getattr(obj.assets_file, "name", "").startswith("CAB-"):
            old_cab = obj.assets_file.name
            break
    new_cab = "CAB-demolishorgskabam00011223344"
    print(f"[*] Remapping CAB: {old_cab} -> {new_cab}")

    # 4. Transform Robot Mesh (cha_ironhide_cin_rotf_00)
    print("[*] Transforming Demolishor Robot mesh stream 0...")
    robot_mesh_copy, r_bounds = transform_mesh_stream0(robot_mesh_tree, "cha_ironhide_cin_rotf_00", reordered_robot_bindposes)

    # 5. Transform Vehicle Mesh (cha_ironhide_cin_rotf_01) if available
    vh_mesh_copy = None
    vh_bounds = None
    if vh_mesh_tree is not None:
        print("[*] Transforming Demolishor Vehicle (Tank) mesh stream 0...")
        vh_mesh_copy, vh_bounds = transform_mesh_stream0(vh_mesh_tree, "cha_ironhide_cin_rotf_01", iron_vh_bindposes)

    # 6. Textures
    tex_dir = root / "tools" / "demolishor" / "textures_processed"
    tex_diffuse = tex_dir / "cha_demolishor_main_a.png"
    tex_normal = tex_dir / "cha_demolishor_main_NM.png"
    tex_raoe = tex_dir / "cha_demolishor_main_tform_misc_RAOE.png"

    vh_diffuse = tex_dir / "cha_demolishor_vh_a.png"
    vh_normal = tex_dir / "cha_demolishor_vh_NM.png"
    vh_raoe = tex_dir / "cha_demolishor_vh_tform_misc_RAOE.png"

    # 7. Apply replacements
    replaced_robot = False
    replaced_vh = False
    routed_smrs = 0

    for obj in i_env.objects:
        if obj.type.name == "Mesh":
            m_tree = obj.read_typetree()
            m_name = m_tree.get("m_Name")
            if m_name == "cha_ironhide_cin_rotf_00":
                print(f"[*] Replacing Ironhide body mesh with Demolishor Robot mesh...")
                replace_str_in_tree(robot_mesh_copy, old_cab, new_cab)
                obj.save_typetree(robot_mesh_copy)
                replaced_robot = True
                print("[✓] Replaced Robot SkinnedMesh successfully!")
            elif m_name == "cha_ironhide_cin_rotf_01" and vh_mesh_copy is not None:
                print(f"[*] Replacing Ironhide truck mesh with Demolishor Tank mesh...")
                replace_str_in_tree(vh_mesh_copy, old_cab, new_cab)
                obj.save_typetree(vh_mesh_copy)
                replaced_vh = True
                print("[✓] Replaced Vehicle SkinnedMesh successfully!")

        elif obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            mesh_pid = smr.get("m_Mesh", {}).get("m_PathID")
            
            # Robot SMR (80 bones)
            if len(smr.get("m_Bones", [])) == 80:
                pref_tr = p1_transforms if obj.path_id == 3131805236270788271 else p2_transforms
                pref_label = "Prefab 1" if obj.path_id == 3131805236270788271 else "Prefab 2"
                new_bones = []
                for bname in robot_bone_names:
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
                print(f"[✓] Re-routed Robot SMR in {pref_label}!")

            # Vehicle SMR (47 bones)
            elif len(smr.get("m_Bones", [])) == 47 and vh_bounds is not None:
                pref_tr = p1_transforms if obj.path_id in (8887288183430146843, 3131805236270788271) else p2_transforms
                pref_label = "Vehicle SMR"
                # Keep original 47 bone structure mapped to BodyBase
                smr["m_AABB"] = {
                    'm_Center': {'x': vh_bounds['center_x'], 'y': vh_bounds['center_y'], 'z': vh_bounds['center_z']},
                    'm_Extent': {'x': vh_bounds['extent_x'], 'y': vh_bounds['extent_y'], 'z': vh_bounds['extent_z']}
                }
                replace_str_in_tree(smr, old_cab, new_cab)
                obj.save_typetree(smr)
                routed_smrs += 1
                print(f"[✓] Updated Vehicle SMR AABB bounds!")

        elif obj.type.name == "Texture2D":
            t_tree = obj.read_typetree()
            t_name = t_tree.get("m_Name", "")
            # Robot Textures
            if t_name == "cha_ironhide_cin_rotf_main_a" and tex_diffuse.is_file():
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
            # Vehicle Textures
            elif t_name == "tform_misc_A" and vh_diffuse.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_diffuse).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Vehicle Diffuse: {t_name}")
            elif t_name == "tform_misc_NM" and vh_normal.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_normal).convert("RGBA")
                tex.save()
                print(f"[✓] Replaced Vehicle Normal: {t_name}")
            elif t_name == "wpns_RAOE" and vh_raoe.is_file():
                tex = obj.read()
                tex.image = Image.open(vh_raoe).convert("RGB")
                tex.save()
                print(f"[✓] Replaced Vehicle RAOE: {t_name}")
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
                if isinstance(first, str) and "ironhide_cin_rotf" in first:
                    first = first.replace("ironhide_cin_rotf", "demolishor_gs")
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
    print(f"\n[✓] SUCCESS: Demolishor Dual-Form AssetBundle created: {output_bundle_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()
