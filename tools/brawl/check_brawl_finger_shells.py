import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from collections import deque

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arml = bpy.data.objects.get("RB_Brawl_CHARSKEL_ArmLoL.mo.dmx")
arm = bpy.data.objects.get("brawl_ARM")
vg_map = {vg.name: vg.index for vg in arml.vertex_groups}

# Build vertex adjacency
adj = [set() for _ in range(len(arml.data.vertices))]
for e in arml.data.edges:
    a, b = e.vertices[0], e.vertices[1]
    adj[a].add(b); adj[b].add(a)

def find_shells(vset):
    seen = set()
    shells = []
    for start in sorted(vset):
        if start in seen: continue
        comp = []
        q = deque([start])
        seen.add(start)
        while q:
            u = q.popleft()
            comp.append(u)
            for nb in adj[u]:
                if nb in vset and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        shells.append(comp)
    return shells

for fn in ["thumb", "index", "middle", "ring", "pinky"]:
    for ph in ["0", "1"]:
        bn = f"bip_{fn}_{ph}_L"
        idx = vg_map.get(bn, -1)
        if idx < 0:
            print(f"{bn:18s}: NOT IN VG")
            continue
        vset = {v.index for v in arml.data.vertices if any(g.group == idx and g.weight > 0.25 for g in v.groups)}
        shells = find_shells(vset)
        sizes = [len(s) for s in shells]
        print(f"{bn:18s}: verts={len(vset):3d}, shells={len(shells)}, sizes={sizes}")
