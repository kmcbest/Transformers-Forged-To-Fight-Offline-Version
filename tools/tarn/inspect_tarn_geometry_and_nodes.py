import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import bmesh

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

print("=== DETAILED INSPECTION OF TOP POLYGON OBJECTS ===")
for name in ["Sphere.001", "Plane.050", "Cube.049", "Cube.019", "Cylinder.045", "Torus.000", "Cylinder.001", "Cylinder.002", "Cube.020", "Cube.025", "Cylinder.038", "Cylinder.062", "Cube.030", "Circle.000", "Cylinder.003", "Cylinder.004", "Plane.012", "Plane.036", "Plane.004", "Plane.008", "Plane.009", "Plane.010", "Plane.058", "Plane.059", "Plane.061", "Plane.002", "Plane.003", "Plane.007"]:
    o = bpy.data.objects.get(name)
    if not o or o.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    verts_before = len(bm.verts)
    polys_before = len(bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    verts_after = len(bm.verts)
    non_man = sum(1 for e in bm.edges if not e.is_manifold)
    loose_v = sum(1 for v in bm.verts if not v.link_faces)
    bm.free()
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = [round(min(p[i] for p in pts), 1) for i in range(3)]
    mx = [round(max(p[i] for p in pts), 1) for i in range(3)]
    print(f"  {name:14s}: verts={verts_before:6d} -> weld={verts_after:6d} | polys={polys_before:6d} | non_man_edges={non_man:5d} | loose={loose_v:3d} | min={mn} max={mx}")

print("\n=== CHECK MATERIAL NODE DETAILS FOR KEY MATERIALS ===")
for mname in ["Material.000", "Material.001", "Material.011", "Material.013", "Material.014", "Material.015", "Material.017", "Material.019", "Material.026", "Material.029", "Material.031", "Material.035", "a metall.000", "a metall.004"]:
    mat = bpy.data.materials.get(mname)
    if not mat or not mat.use_nodes:
        continue
    print(f"\nMaterial: {mname}")
    for l in mat.node_tree.links:
        fn = l.from_node.name
        fs = l.from_socket.name
        tn = l.to_node.name
        ts = l.to_socket.name
        extra = ""
        if l.from_node.type == 'TEX_IMAGE' and l.from_node.image:
            extra = f" [img={l.from_node.image.name}]"
        elif l.from_node.type == 'MIX_SHADER':
            extra = f" [fac={l.from_node.inputs[0].default_value:.2f}]"
        print(f"  {fn}.{fs}{extra} -> {tn}.{ts}")
    for n in mat.node_tree.nodes:
        if n.type == 'MIX_SHADER':
            print(f"  [Node {n.name}] fac_linked={n.inputs[0].is_linked}, fac_val={n.inputs[0].default_value:.3f}")
        elif n.type == 'BSDF_PRINCIPLED':
            print(f"  [Node {n.name}] base={tuple(round(x,2) for x in n.inputs['Base Color'].default_value)}, met={n.inputs['Metallic'].default_value:.2f}, rough={n.inputs['Roughness'].default_value:.2f}")
