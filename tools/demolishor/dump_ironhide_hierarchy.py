# -*- coding: utf-8 -*-
import sys
import json
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

# Map PathID to GameObject name
go_names = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        go_names[obj.path_id] = tree.get("m_Name")

# Collect all Transforms
transforms = {}
root_pids = []
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_pid = t.get("m_GameObject", {}).get("m_PathID")
        name = go_names.get(go_pid, f"Unknown_{go_pid}")
        father_pid = t.get("m_Father", {}).get("m_PathID", 0)
        children = [c.get("m_PathID") for c in t.get("m_Children", [])]
        
        transforms[obj.path_id] = {
            "path_id": obj.path_id,
            "name": name,
            "father_pid": father_pid,
            "children_pids": children,
            "localPosition": t.get("m_LocalPosition", {}),
            "localRotation": t.get("m_LocalRotation", {}),
            "localScale": t.get("m_LocalScale", {})
        }
        if father_pid == 0:
            root_pids.append(obj.path_id)

print(f"Total Transforms: {len(transforms)}")
print(f"Root Transforms ({len(root_pids)}):")
for r in root_pids:
    print(f"  Root: {transforms[r]['name']} (PID: {r})")

out_file = Path("tools/demolishor/ironhide_extracted/ironhide_transforms.json")
out_file.parent.mkdir(parents=True, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(transforms, f, indent=2)
print(f"[✓] Saved hierarchy to {out_file}")
