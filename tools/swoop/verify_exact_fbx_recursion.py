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

elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')
connections = next(e for e in elem.elems if e.id == b'Connections')

models = {}
lcl_scales = {}
clusters_tl = {}

for e in objects.elems:
    if e.id == b'Model':
        uid = e.props[0]
        name = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        models[uid] = name
        p70 = next((s for s in e.elems if s.id == b'Properties70'), None)
        sca = Vector((1.0, 1.0, 1.0))
        if p70:
            for p in p70.elems:
                pname = p.props[0].decode('utf-8', errors='replace')
                if pname == 'Lcl Scaling':
                    sca = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
        lcl_scales[name] = sca
    elif e.id == b'Deformer' and len(e.props) >= 3 and e.props[2] == b'Cluster':
        uid = e.props[0]
        for sub in e.elems:
            if sub.id == b'TransformLink':
                clusters_tl[uid] = sub.props[0]

c_tl = {}
for c in connections.elems:
    if c.id == b'C':
        src, dst = c.props[1], c.props[2]
        if src in models and dst in clusters_tl:
            bname = models[src]
            tl = clusters_tl[dst]
            c_tl[bname] = Matrix([tl[0:4], tl[4:8], tl[8:12], tl[12:16]]).transposed()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Compute W_true(0) recursively from unmodified Blender EditBone.matrix_local and FBX Lcl Scaling
def scale_mat(s: Vector) -> Matrix:
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = s.x, s.y, s.z
    return m

w_true_0 = {}
def get_w_true_0(b):
    if b.name in w_true_0:
        return w_true_0[b.name]
    s = lcl_scales.get(b.name, Vector((1.0, 1.0, 1.0)))
    if b.parent is None:
        eb_rel = b.matrix_local
        w = arm.matrix_world @ eb_rel @ scale_mat(s)
    else:
        eb_rel = b.parent.matrix_local.inverted() @ b.matrix_local
        w = get_w_true_0(b.parent) @ eb_rel @ scale_mat(s)
    w_true_0[b.name] = w
    return w

max_pos_err = 0.0
max_sca_err = 0.0
for b in arm.data.bones:
    w0 = Matrix.Scale(100.0, 4) @ get_w_true_0(b)
    if b.name in c_tl:
        tl = c_tl[b.name]
        # Note: compare translation & scale
        l_w, r_w, s_w = w0.decompose()
        l_t, r_t, s_t = tl.decompose()
        pe = (l_w - l_t).length
        se = (s_w - s_t).length
        if pe > max_pos_err:
            max_pos_err = pe
        if se > max_sca_err:
            max_sca_err = se
        if pe > 1e-3 or se > 1e-3:
            print(f"  Mismatch on {b.name}: pos_w={l_w} vs pos_tl={l_t}, sca_w={s_w} vs sca_tl={s_t}")

print(f"Checked all {len(c_tl)} clustered bones against FBX TransformLink:")
print(f"  max_pos_err = {max_pos_err:.6f}")
print(f"  max_sca_err = {max_sca_err:.6f}")
