# -*- coding: utf-8 -*-
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

with open("tools/demolishor/ironhide_extracted/ironhide_transforms.json", "r", encoding="utf-8") as f:
    transforms = json.load(f)

root_pid = "5877212488468470809"

def print_tree(pid, indent=0):
    node = transforms.get(str(pid))
    if not node: return
    name = node["name"]
    pos = node["localPosition"]
    rot = node["localRotation"]
    print("  " * indent + f"- {name} (pos: [{pos.get('x',0):.2f}, {pos.get('y',0):.2f}, {pos.get('z',0):.2f}])")
    for child_pid in node["children_pids"]:
        print_tree(child_pid, indent + 1)

print("=== IronHide_Cin_ROTF Hierarchy ===")
print_tree(root_pid)
