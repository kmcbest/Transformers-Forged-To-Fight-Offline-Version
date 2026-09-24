import bpy
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
for vg in mesh.vertex_groups:
    if "Head" in vg.name or "Face" in vg.name or "Spine00" in vg.name:
        pts = [v.co for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.5]
        if pts:
            avg = sum(pts, mathutils.Vector((0, 0, 0))) / len(pts)
            print(f"VG {vg.name:25s}: avg=({avg.x:6.2f}, {avg.y:6.2f}, {avg.z:6.2f})")
