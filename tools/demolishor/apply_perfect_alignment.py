# -*- coding: utf-8 -*-
import sys
import struct
import copy
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

print("=== Transforming Demolishor Mesh to Perfect Rest Pose Alignment ===")

# 1. Load Ironhide bundle for ground-truth bindposes
env_i = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
iron_bindposes = None
for obj in env_i.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            iron_bindposes = tree.get('m_BindPose', [])
            break

go_names = {}
tr_to_go = {}
for obj in env_i.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

iron_smr_bones = []
for obj in env_i.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 80:
            for b in bones:
                tr_id = b.get('m_PathID')
                iron_smr_bones.append(go_names.get(tr_to_go.get(tr_id)))
            break

print(f"[+] Ironhide has {len(iron_smr_bones)} bones and {len(iron_bindposes)} bindposes.")

# 2. Load Demolishor bundle
bundle_path = 'assets_redeco/demolishor_gs.assetbundle'
env_d = UnityPy.load(bundle_path)

demo_go_names = {}
demo_tr_to_go = {}
for obj in env_d.objects:
    if obj.type.name == 'GameObject':
        demo_go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        demo_tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

demo_smr_bones = []
for obj in env_d.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 80:
            for b in bones:
                tr_id = b.get('m_PathID')
                demo_smr_bones.append(demo_go_names.get(demo_tr_to_go.get(tr_id)))
            break

print(f"[+] Demolishor SMR has {len(demo_smr_bones)} bones.")

# 3. Create reordered bindposes
reordered_bindposes = []
for j, bname in enumerate(demo_smr_bones):
    if bname in iron_smr_bones:
        iron_idx = iron_smr_bones.index(bname)
        reordered_bindposes.append(copy.deepcopy(iron_bindposes[iron_idx]))
    else:
        raise ValueError(f"Bone {bname} not found in Ironhide bones!")

print(f"[✓] Reordered all 80 bindposes matching Demolishor's bone indexing!")

# 4. Modify Mesh in Demolishor bundle
for obj in env_d.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            print(f"[*] Processing Mesh: {tree.get('m_Name')}")
            
            # Set reordered bindposes
            tree['m_BindPose'] = reordered_bindposes
            
            # Transform Stream 0 vertices
            vdata = tree.get('m_VertexData', {})
            v_count = vdata.get('m_VertexCount', 0)
            raw_data = bytearray(vdata.get('m_DataSize', []))
            stride = 40  # stream 0 stride: 12 pos + 12 norm + 16 tan
            
            print(f"[*] Transforming {v_count} vertices in stream 0 (stride {stride})...")
            
            min_x, max_x = float('inf'), float('-inf')
            min_y, max_y = float('inf'), float('-inf')
            min_z, max_z = float('inf'), float('-inf')
            
            for i in range(v_count):
                offset = i * stride
                # Read pos: x, y, z
                px, py, pz = struct.unpack_from('<3f', raw_data, offset)
                # Read norm: nx, ny, nz
                nx, ny, nz = struct.unpack_from('<3f', raw_data, offset + 12)
                # Read tan: tx, ty, tz, tw
                tx, ty, tz, tw = struct.unpack_from('<4f', raw_data, offset + 24)
                
                # Transform: X_new = px, Y_new = pz, Z_new = -py
                new_px = px
                new_py = pz
                new_pz = -py
                
                new_nx = nx
                new_ny = nz
                new_nz = -ny
                
                new_tx = tx
                new_ty = tz
                new_tz = -ty
                
                struct.pack_into('<3f', raw_data, offset, new_px, new_py, new_pz)
                struct.pack_into('<3f', raw_data, offset + 12, new_nx, new_ny, new_nz)
                struct.pack_into('<4f', raw_data, offset + 24, new_tx, new_ty, new_tz, tw)
                
                min_x = min(min_x, new_px); max_x = max(max_x, new_px)
                min_y = min(min_y, new_py); max_y = max(max_y, new_py)
                min_z = min(min_z, new_pz); max_z = max(max_z, new_pz)
            
            vdata['m_DataSize'] = bytes(raw_data)
            tree['m_VertexData'] = vdata
            
            # Update AABB
            center_x = (min_x + max_x) / 2.0
            center_y = (min_y + max_y) / 2.0
            center_z = (min_z + max_z) / 2.0
            extent_x = (max_x - min_x) / 2.0
            extent_y = (max_y - min_y) / 2.0
            extent_z = (max_z - min_z) / 2.0
            
            tree['m_LocalAABB'] = {
                'm_Center': {'x': center_x, 'y': center_y, 'z': center_z},
                'm_Extent': {'x': extent_x, 'y': extent_y, 'z': extent_z}
            }
            
            print(f"[✓] New Mesh Bounds:")
            print(f"    X: [{min_x:.2f}, {max_x:.2f}] (width: {max_x-min_x:.2f})")
            print(f"    Y: [{min_y:.2f}, {max_y:.2f}] (HEIGHT: {max_y-min_y:.2f})")
            print(f"    Z: [{min_z:.2f}, {max_z:.2f}] (depth: {max_z-min_z:.2f})")
            
            obj.save_typetree(tree)
            break

# Also update SMR bounds
for obj in env_d.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 80:
            tree['m_AABB'] = {
                'm_Center': {'x': center_x, 'y': center_y, 'z': center_z},
                'm_Extent': {'x': extent_x, 'y': extent_y, 'z': extent_z}
            }
            obj.save_typetree(tree)

print("[*] Saving modified AssetBundle with packer='lz4'...")
with open(bundle_path, 'wb') as f:
    f.write(env_d.file.save(packer='lz4'))

print(f"[✓] SUCCESS: Updated {bundle_path} successfully!")
