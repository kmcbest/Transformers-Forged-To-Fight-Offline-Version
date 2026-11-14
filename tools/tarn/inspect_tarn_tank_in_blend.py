import sys
import bpy
import numpy as np
from mathutils import Vector

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\06_working\tarn_workspace_baked.blend")
for nm in ("TarnTank_Mesh", "TarnTankTreadL_Mesh", "TarnTankTreadR_Mesh"):
    o = bpy.data.objects.get(nm)
    if not o:
        print(f"MISSING {nm}")
        continue
    pts = np.array([[ (o.matrix_world @ v.co).x, (o.matrix_world @ v.co).y, (o.matrix_world @ v.co).z ] for v in o.data.vertices])
    uvs = [uv.name for uv in o.data.uv_layers]
    mats = [s.material.name if s.material else None for s in o.material_slots]
    print(f"{nm:22s}: parent={o.parent.name if o.parent else None} loc={tuple(round(x,3) for x in o.location)} scl={tuple(round(x,3) for x in o.scale)} verts={len(o.data.vertices)} polys={len(o.data.polygons)} uvs={uvs} mats={mats}")
    print(f"  world X=[{pts[:,0].min():.3f},{pts[:,0].max():.3f}] Y=[{pts[:,1].min():.3f},{pts[:,1].max():.3f}] Z=[{pts[:,2].min():.3f},{pts[:,2].max():.3f}]")
