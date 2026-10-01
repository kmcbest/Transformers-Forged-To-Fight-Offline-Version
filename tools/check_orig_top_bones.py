import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}

# In Blender FBX import, Demolishor might be Y up or Z up
verts_sorted_z = sorted(mesh.data.vertices, key=lambda v: v.co.z, reverse=True)
print(f"Original Demolishor mesh vertices: {len(mesh.data.vertices)}")
print(f"Highest Z: {verts_sorted_z[0].co.z:.2f}, lowest Z: {verts_sorted_z[-1].co.z:.2f}")

orig_bone_counts = {}
for v in verts_sorted_z[:600]:
    for g in v.groups:
        if g.weight > 0.2:
            bname = vg_names.get(g.group, "unknown")
            orig_bone_counts[bname] = orig_bone_counts.get(bname, 0) + 1

print("\nOriginal bones for top vertices:")
for b, c in sorted(orig_bone_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
    print(f"  {b:30s}: {c} vertices")
