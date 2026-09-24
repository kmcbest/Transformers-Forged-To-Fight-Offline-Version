import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
leg_groups = [vg.name for vg in mesh.vertex_groups if any(k in vg.name for k in ['Leg', 'Thigh', 'Knee', 'Ankle', 'Toe', 'Foot'])]
print(f"Total leg groups ({len(leg_groups)}):")
for g in sorted(leg_groups):
    vg = mesh.vertex_groups[g]
    cnt = sum(1 for v in mesh.data.vertices for grp in v.groups if grp.group == vg.index and grp.weight > 0.01)
    print(f"  {g:25s}: {cnt:4d} verts")

# Also check other groups that might contain lower body / pelvis / groin / leg parts!
all_other = [vg.name for vg in mesh.vertex_groups if vg.name not in leg_groups and not any(k in vg.name for k in ['Arm', 'Hand', 'Finger', 'Elbow', 'Shoulder', 'Head', 'Neck', 'Face', 'Jaw'])]
print(f"\nOther lower body / spine groups ({len(all_other)}):")
for g in sorted(all_other):
    vg = mesh.vertex_groups[g]
    cnt = sum(1 for v in mesh.data.vertices for grp in v.groups if grp.group == vg.index and grp.weight > 0.01)
    print(f"  {g:25s}: {cnt:4d} verts")
