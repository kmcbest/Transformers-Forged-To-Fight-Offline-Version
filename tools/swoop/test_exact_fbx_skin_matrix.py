import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from io_scene_fbx import parse_fbx
from mathutils import Matrix, Vector

FBX_SRC = Path(r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")

# Read Cluster Transform and TransformLink from raw FBX
elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')
connections = next(e for e in elem.elems if e.id == b'Connections')

models = {}
model_props = {}
clusters_tl = {}
clusters_t = {}

for e in objects.elems:
    if e.id == b'Model':
        uid = e.props[0]
        name = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        models[uid] = name
        p70 = next((s for s in e.elems if s.id == b'Properties70'), None)
        props = {}
        if p70:
            for p in p70.elems:
                pname = p.props[0].decode('utf-8', errors='replace')
                props[pname] = p.props[4:]
        model_props[name] = props
    elif e.id == b'Deformer' and len(e.props) >= 3 and e.props[2] == b'Cluster':
        uid = e.props[0]
        for sub in e.elems:
            if sub.id == b'TransformLink':
                clusters_tl[uid] = sub.props[0]
            elif sub.id == b'Transform':
                clusters_t[uid] = sub.props[0]

c_tl = {}
c_t = {}
for c in connections.elems:
    if c.id == b'C':
        src, dst = c.props[1], c.props[2]
        if src in models and dst in clusters_tl:
            bname = models[src]
            c_tl[bname] = clusters_tl[dst]
            c_t[bname] = clusters_t[dst]

for bname in ["Bip001 Spine1", "Bone_Spine1", "bird_chest", "bird_neck", "bird_Head", "bird_Head_02", "beak", "beak_the bottom", "Bone_Head", "Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)"]:
    print(f"=== {bname} ===")
    print(f"  Model props: {model_props.get(bname, {})}")
    if bname in c_tl:
        tl = c_tl[bname]
        m_tl = Matrix([tl[0:4], tl[4:8], tl[8:12], tl[12:16]]).transposed()
        loc, rot, sca = m_tl.decompose()
        print(f"  TransformLink: loc={[round(x,4) for x in loc]} rot={[round(x,4) for x in rot]} sca={[round(x,4) for x in sca]}")
