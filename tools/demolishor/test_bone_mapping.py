# -*- coding: utf-8 -*-
import bpy
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Demolishor_ARM")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

print(f"Demolishor Mesh vertex groups: {len(mesh.vertex_groups)}")

# Inspect the parent chain for each bone in arm
def get_main_ancestor(bone):
    cur = bone
    while cur:
        if cur.name.endswith("_XB") or "Toes" in cur.name or "Finger" in cur.name:
            return cur.name
        cur = cur.parent
    return None

mapping = {}
for b in arm.data.bones:
    ancestor = get_main_ancestor(b)
    mapping[b.name] = ancestor

print("\n--- Bone to Main Ancestor Mapping (Sample 30) ---")
for k, v in list(mapping.items())[:30]:
    if k != v:
        print(f"  {k} -> {v}")
