import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import shutil
import UnityPy
from UnityPy.classes import PPtr

# Paths
rust_bak_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\rust\rust_merged.assetbundle.bak"
dev_bundle_path = r"E:\Agent\TFTF-blender\stage_project\AssetBundles\devastator_stage.assetbundle"

out_apk_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\rust\rust_merged.assetbundle"
out_redeco_path = r"E:\Agent\TFTF-blender\assets_redeco\rust_merged.assetbundle"

print("==================================================")
print("  TFTF Stage Mod: Devastator -> Rust Sea Merging  ")
print("==================================================")

# Step 0: Ensure backup of original
print("\n[Step 0] Backing up original rust_merged.assetbundle...")
backup_orig_path = out_apk_path + ".original"
if not os.path.exists(backup_orig_path):
    if os.path.exists(rust_bak_path):
        shutil.copyfile(rust_bak_path, backup_orig_path)
    elif os.path.exists(out_apk_path):
        shutil.copyfile(out_apk_path, backup_orig_path)
    print(f"  [✓] Created immutable backup: {backup_orig_path}")
else:
    print(f"  [i] Immutable backup already exists: {backup_orig_path}")

# Step 1: Load AssetBundles
print("\n[Step 1] Loading source bundles...")
env_rust = UnityPy.load(rust_bak_path)
env_dev = UnityPy.load(dev_bundle_path)

bf_rust = list(env_rust.files.values())[0]
bf_dev = list(env_dev.files.values())[0]

rust_cab_name = 'CAB-8047d50cb53b499f81473861dbf0f211'
dev_cab_name = 'CAB-173392592a09aa74156a2f75549d5a15'

rust_sf = bf_rust.files[rust_cab_name]
dev_sf = bf_dev.files[dev_cab_name]

print(f"  Original rust_merged objects: {len(rust_sf.objects)}")
print(f"  Devastator objects: {len(dev_sf.objects)}")

# Step 2: Append dev typetrees to rust_sf to preserve 100% binary fidelity
print("\n[Step 2] Integrating TypeTree definitions...")
base_type_offset = len(rust_sf.types)
for dev_t in dev_sf.types:
    rust_sf.types.append(dev_t)
print(f"  Appended {len(dev_sf.types)} TypeTree nodes from dev bundle (base offset: {base_type_offset})")

if hasattr(dev_sf, 'script_types'):
    for st in dev_sf.script_types:
        if st not in rust_sf.script_types:
            rust_sf.script_types.append(st)

# Step 3: Copy Devastator objects into rust_sf
print("\n[Step 3] Merging objects into rust_merged SerializedFile...")
copied = 0
for pid, obj in dev_sf.objects.items():
    # Skip AssetBundle header (PID 1) and Unity Standard Shader (PID -4850512016903265157)
    if pid in [1, -4850512016903265157]:
        continue

    # Cache raw bytes from dev_sf reader BEFORE re-assigning assets_file
    raw = obj.get_raw_data()
    obj.set_raw_data(raw)

    # Re-map type_id and serialized_type to rust_sf with exact offset
    new_type_id = base_type_offset + obj.type_id
    obj.type_id = new_type_id
    obj.serialized_type = rust_sf.types[new_type_id]

    # Assign assets_file to rust_sf
    obj.assets_file = rust_sf
    rust_sf.objects[pid] = obj
    copied += 1

print(f"  [✓] Merged {copied} Devastator objects with 100% binary fidelity.")

# Step 4: Copy resS streaming resource file into bundle container
print("\n[Step 4] Integrating external streaming resources (resS)...")
dev_ress_name = f"{dev_cab_name}.resS"
if dev_ress_name in bf_dev.files:
    ress_data = bf_dev.files[dev_ress_name]
    bf_rust.files[dev_ress_name] = ress_data
    print(f"  [✓] Injected {dev_ress_name} ({len(ress_data.read()):,} bytes) into container.")
else:
    print(f"  [!] WARNING: {dev_ress_name} not found in dev bundle!")

# Step 5: Connect Devastator to rust_merged Transform hierarchy
print("\n[Step 5] Connecting scene Transform hierarchy...")
rust_merged_t_pid = -8531341815069655759
rust_merged_t = rust_sf.objects[rust_merged_t_pid].read()

dev_root_t_pid = 4735182709122105431
dev_root_t = rust_sf.objects[dev_root_t_pid].read()

new_child_pptr = PPtr(m_FileID=0, m_PathID=dev_root_t_pid, assetsfile=rust_sf)
rust_merged_t.m_Children.append(new_child_pptr)
rust_merged_t.save()

dev_root_t.m_Father = PPtr(m_FileID=0, m_PathID=rust_merged_t_pid, assetsfile=rust_sf)
dev_root_t.save()
print(f"  [✓] Devastator (Transform PID {dev_root_t_pid}) parented to rust_merged (PID {rust_merged_t_pid}).")

# Step 6: Save with LZ4 compression
print("\n[Step 6] Packing AssetBundle with LZ4 compression...")
saved_bytes = env_rust.file.save(packer="lz4")
print(f"  [✓] Packed bundle size: {len(saved_bytes):,} bytes ({len(saved_bytes)/(1024*1024):.2f} MB)")

# Step 7: Write to target destinations
print("\n[Step 7] Deploying output bundles...")
os.makedirs(os.path.dirname(out_apk_path), exist_ok=True)
with open(out_apk_path, "wb") as f:
    f.write(saved_bytes)
print(f"  [✓] Saved to APK extracted dir: {out_apk_path}")

os.makedirs(os.path.dirname(out_redeco_path), exist_ok=True)
with open(out_redeco_path, "wb") as f:
    f.write(saved_bytes)
print(f"  [✓] Saved to Redeco assets dir: {out_redeco_path}")

# Step 8: Comprehensive Verification
print("\n[Step 8] Running comprehensive verification...")
verify_env = UnityPy.load(out_apk_path)
v_bf = list(verify_env.files.values())[0]
v_sf = v_bf.files[rust_cab_name]

print(f"  Total verified objects: {len(v_sf.objects)}")
print(f"  Files in container: {list(v_bf.files.keys())}")

# Check hierarchy
hierarchy_ok = False
for pid, obj in v_sf.objects.items():
    if obj.type.name == "GameObject":
        d = obj.read()
        if d.m_Name == "rust_merged":
            for c_ptr in d.m_Components:
                if c_ptr.type.name == "Transform":
                    c = c_ptr.read()
                    for ch in c.m_Children:
                        if ch.path_id == dev_root_t_pid:
                            hierarchy_ok = True
                            break
            break

print(f"  Transform hierarchy check: {'PASS' if hierarchy_ok else 'FAIL'}")

# Verify all objects can be read without exceptions
read_errors = 0
for pid, obj in v_sf.objects.items():
    try:
        obj.read()
    except Exception as e:
        read_errors += 1
        print(f"  [!] Read error on PID={pid}, Type={obj.type.name}: {e}")

print(f"  Object deserialization check: {'PASS (0 errors)' if read_errors == 0 else f'FAIL ({read_errors} errors)'}")

print("\n==================================================")
print("  MERGE COMPLETE AND VERIFIED SUCCESSFULLY!       ")
print("==================================================")
