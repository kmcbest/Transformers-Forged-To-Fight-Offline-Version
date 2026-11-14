import sys
import bpy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_cleaned.blend")
robot = bpy.data.objects["Tarn_Robot_LowPoly"]
print("Material slots on Tarn_Robot_LowPoly:")
mat_polys = {}
for p in robot.data.polygons:
    mat_polys[p.material_index] = mat_polys.get(p.material_index, 0) + 1
for i, s in enumerate(robot.material_slots):
    m = s.material
    pc = mat_polys.get(i, 0)
    # check centroid Z/Y of polys with this material
    zs = [robot.data.vertices[p.vertices[0]].co.z for p in robot.data.polygons if p.material_index == i]
    zinfo = f"Z=[{min(zs):.2f},{max(zs):.2f}]" if zs else "empty"
    print(f"  [{i:2d}] {m.name if m else 'None':20s} polys={pc:5d} {zinfo}")
    if m and m.use_nodes and (pc < 400 or "005" in m.name or "015" in m.name or "009" in m.name):
        for n in m.node_tree.nodes:
            if n.type in ("BSDF_PRINCIPLED", "EMISSION", "BSDF_GLOSSY"):
                bc = tuple(round(x, 3) for x in n.inputs[0].default_value) if len(n.inputs) > 0 and hasattr(n.inputs[0], "default_value") else None
                em = tuple(round(x, 3) for x in n.inputs["Emission"].default_value) if "Emission" in n.inputs else None
                print(f"       node {n.type}: col={bc} emit={em}")
