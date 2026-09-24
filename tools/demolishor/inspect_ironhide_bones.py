# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

# Find the SMR for cha_ironhide_cin_rotf_00
target_smr = None
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        mesh_ptr = tree.get("m_Mesh", {})
        # Find mesh name
        for m_obj in env.objects:
            if m_obj.path_id == mesh_ptr.get("m_PathID") and m_obj.type.name == "Mesh":
                m_tree = m_obj.read_typetree()
                if m_tree.get("m_Name") == "cha_ironhide_cin_rotf_00":
                    target_smr = tree
                    break
        if target_smr:
            break

if not target_smr:
    print("Could not find SMR for cha_ironhide_cin_rotf_00")
    sys.exit(1)

bones_ptrs = target_smr.get("m_Bones", [])
print(f"Found SMR for cha_ironhide_cin_rotf_00 with {len(bones_ptrs)} bones.")

# Resolve bone names
bone_names = []
path_to_name = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

for b_ptr in bones_ptrs:
    pid = b_ptr.get("m_PathID")
    name = path_to_name.get(pid, f"Unknown_{pid}")
    bone_names.append((pid, name))

print("\n--- Bones List (Sample 30) ---")
for idx, (pid, name) in enumerate(bone_names[:30]):
    print(f"  [{idx:02d}] {name} (PID: {pid})")
print(f"  ... total {len(bone_names)} bones")
