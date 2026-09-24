import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm_groups = [vg.name for vg in mesh.vertex_groups if any(k in vg.name for k in ['Arm', 'Elbow', 'Hand', 'Finger', 'Shoulder', 'Clav', 'Weapon'])]
print(f"Total arm/weapon groups ({len(arm_groups)}):")
for g in sorted(arm_groups):
    vg = mesh.vertex_groups[g]
    cnt = sum(1 for v in mesh.data.vertices for grp in v.groups if grp.group == vg.index and grp.weight > 0.01)
    print(f"  {g:35s}: {cnt} verts")
