import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from io_scene_fbx import parse_fbx
from mathutils import Matrix

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
elem, _ = parse_fbx.parse(str(FBX_SRC))

# Find Objects -> Deformer (Cluster) and Model nodes
objects = next(e for e in elem.elems if e.id == b'Objects')
models = {}
clusters = {}
connections = next(e for e in elem.elems if e.id == b'Connections')

for e in objects.elems:
    if e.id == b'Model':
        uid = e.props[0]
        name = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        models[uid] = (name, e)
    elif e.id == b'Deformer' and len(e.props) >= 3 and e.props[2] == b'Cluster':
        uid = e.props[0]
        name = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        t_mat = None
        tl_mat = None
        for sub in e.elems:
            if sub.id == b'Transform':
                t_mat = sub.props[0]
            elif sub.id == b'TransformLink':
                tl_mat = sub.props[0]
        clusters[uid] = (name, t_mat, tl_mat)

# Map cluster -> bone model via connections
c_to_m = {}
for c in connections.elems:
    if c.id == b'C':
        src, dst = c.props[1], c.props[2]
        if src in models and dst in clusters:
            c_to_m[dst] = models[src][0]

for cuid, (cname, t_mat, tl_mat) in clusters.items():
    bname = c_to_m.get(cuid, cname)
    if any(k in bname for k in ["Wing", "bird", "beak", "Back", "Spine1", "Head"]):
        # FBX 4x4 matrix is column-major 16 doubles (translation is indices 12, 13, 14)
        tl_pos = (round(tl_mat[12], 4), round(tl_mat[13], 4), round(tl_mat[14], 4)) if tl_mat else None
        t_pos = (round(t_mat[12], 4), round(t_mat[13], 4), round(t_mat[14], 4)) if t_mat else None
        tl_s0 = round((tl_mat[0]**2 + tl_mat[1]**2 + tl_mat[2]**2)**0.5, 4) if tl_mat else None
        print(f"Cluster Bone '{bname:26s}': TransformLink pos={tl_pos} (scale={tl_s0}) | Transform pos={t_pos}")
