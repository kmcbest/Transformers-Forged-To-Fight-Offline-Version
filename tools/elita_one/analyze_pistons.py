import bpy

fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = bpy.data.objects['SK_CH_11.001']

def analyze_vg(name):
    vg = mesh_obj.vertex_groups.get(name)
    if not vg: return
    verts = [v for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.5 for g in v.groups)]
    if not verts: return
    zs = [v.co.z for v in verts]
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    print(f"VG '{name}': {len(verts)} verts, Z=[{min(zs):.2f}, {max(zs):.2f}], X=[{min(xs):.2f}, {max(xs):.2f}], Y=[{min(ys):.2f}, {max(ys):.2f}]")

print("--- Ankle parts ---")
analyze_vg('l_foot_skin')
analyze_vg('l_lowerleg_skin')
analyze_vg('l_piston_leg_start_01_skin')
analyze_vg('l_piston_leg_start_02_skin')
analyze_vg('l_piston_leg_end_01_skin1')
analyze_vg('l_piston_leg_end_02_skin2')

print("--- Hip pistons ---")
analyze_vg('l_upperleg_skin')
analyze_vg('pelvis_skin')
analyze_vg('l_piston_leg_start_01_skin3')
analyze_vg('l_piston_leg_start_02_skin4')
analyze_vg('l_piston_leg_end_01_skin')
analyze_vg('l_piston_leg_end_02_skin')
