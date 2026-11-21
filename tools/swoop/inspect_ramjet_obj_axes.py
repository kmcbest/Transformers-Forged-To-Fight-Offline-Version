import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Read ramjet_official_00.obj
verts = []
with open("3rd-party-models/swoop/01_master/ramjet_official_00.obj", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("v "):
            parts = line.strip().split()[1:]
            verts.append([float(p) for p in parts])

xs = [v[0] for v in verts]
ys = [v[1] for v in verts]
zs = [v[2] for v in verts]
print(f"Ramjet 00 OBJ bounds:")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] (span: {max(xs)-min(xs):.3f})")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] (span: {max(ys)-min(ys):.3f})")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] (span: {max(zs)-min(zs):.3f})")
