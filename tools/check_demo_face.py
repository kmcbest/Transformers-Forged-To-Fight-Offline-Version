import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "face", "jaw"])]

head_verts = [v for v in mesh.data.vertices if any(g.group in head_vgs and g.weight > 0.3 for g in v.groups)]
print(f"Total head vertices: {len(head_verts)}")
ys = [v.co.y for v in head_verts]
print(f"Head vertices Y range: {min(ys):.3f} to {max(ys):.3f}, avg: {sum(ys)/len(ys):.3f}")

# Check where Demolishor's visor/eyes are:
# In Demolishor original textures, where is the visor?
# Or let's check chest vs back:
spine_vgs = [vg.index for vg in mesh.vertex_groups if "spine" in vg.name.lower() or "lumbar" in vg.name.lower()]
spine_verts = [v for v in mesh.data.vertices if any(g.group in spine_vgs and g.weight > 0.3 for g in v.groups)]
sys = [v.co.y for v in spine_verts]
print(f"Spine/Torso vertices Y range: {min(sys):.3f} to {max(sys):.3f}, avg: {sum(sys)/len(sys):.3f}")
