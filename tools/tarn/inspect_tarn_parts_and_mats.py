import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
FALLBACK_DIR = TARN_ROOT / "01_robot_source" / "fallback_textures"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

if FALLBACK_DIR.is_dir():
    bpy.ops.file.find_missing_files(directory=str(FALLBACK_DIR))

print("=== HAND ARMATURES & MESHES DETAIL ===")
for aname in ["Armature.000", "Armature.001"]:
    arm = bpy.data.objects.get(aname)
    if arm:
        print(f"Armature {aname}: loc={tuple(round(x,3) for x in arm.location)}, rot={tuple(round(x,3) for x in arm.rotation_euler)}, scale={tuple(round(x,3) for x in arm.scale)}, children={[c.name for c in arm.children]}")
        for b in arm.data.bones:
            hw = arm.matrix_world @ b.head_local
            tw = arm.matrix_world @ b.tail_local
            pname = b.parent.name if b.parent else "None"
            print(f"  bone {b.name:12s} | parent={pname:10s} | head={tuple(round(x,2) for x in hw)} | tail={tuple(round(x,2) for x in tw)}")

for mname in ["Cylinder.001", "Cylinder.002"]:
    o = bpy.data.objects.get(mname)
    if o:
        print(f"Mesh {mname}: parent={o.parent.name if o.parent else 'None'}, loc={tuple(round(x,3) for x in o.location)}, scale={tuple(round(x,3) for x in o.scale)}, mods={[(m.name, m.type, m.show_viewport) for m in o.modifiers]}")
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        mn = [round(min(p[i] for p in pts), 2) for i in range(3)]
        mx = [round(max(p[i] for p in pts), 2) for i in range(3)]
        print(f"  world bbox: min={mn}, max={mx}")

print("\n=== ALL MESHES IN SOURCE BLEND (sorted by base tris desc) ===")
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in sorted(mesh_objs, key=lambda x: -len(x.data.polygons)):
    tris = sum(max(0, len(p.vertices)-2) for p in o.data.polygons)
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = [round(min(p[i] for p in pts), 1) for i in range(3)] if pts else [0,0,0]
    mx = [round(max(p[i] for p in pts), 1) for i in range(3)] if pts else [0,0,0]
    mats = [ms.material.name if ms.material else "None" for ms in o.material_slots]
    mods = [f"{m.type}({m.show_viewport})" for m in o.modifiers]
    print(f"  {o.name:22s} | verts={len(o.data.vertices):6d} | tris={tris:6d} | hide_ren={o.hide_render} | mods={mods} | mats={mats} | min={mn} max={mx}")

print("\n=== MATERIAL NODE TREES SUMMARY ===")
for mat in sorted(bpy.data.materials, key=lambda x: x.name):
    if not mat.use_nodes or not mat.node_tree:
        continue
    nodes_desc = []
    for n in mat.node_tree.nodes:
        if n.type == 'TEX_IMAGE':
            inm = n.image.name if n.image else "NONE"
            isz = tuple(n.image.size) if n.image else (0,0)
            nodes_desc.append(f"TEX({inm}{isz})")
        elif n.type in ('BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'EMISSION', 'MIX_SHADER', 'VALTORGB', 'RGB', 'MIX_RGB'):
            col_s = ""
            if n.type in ('BSDF_PRINCIPLED', 'BSDF_DIFFUSE', 'BSDF_GLOSSY', 'EMISSION'):
                c = n.inputs[0].default_value
                col_s = f"({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})"
            nodes_desc.append(f"{n.type}{col_s}")
    print(f"  {mat.name:20s} -> {', '.join(nodes_desc)}")

print("\n=== COMPONENT AUDIT FOR TOP HEAVY OBJECTS ===")
for mname in ["Cube.049", "Cylinder.045", "Sphere.001", "Plane.050", "Cube.019", "Torus.000"]:
    o = bpy.data.objects.get(mname)
    if o and o.type == 'MESH':
        vcount = len(o.data.vertices)
        adj = [[] for _ in range(vcount)]
        for e in o.data.edges:
            adj[e.vertices[0]].append(e.vertices[1])
            adj[e.vertices[1]].append(e.vertices[0])
        vis = bytearray(vcount)
        comps = 0
        sizes = []
        for i in range(vcount):
            if not vis[i]:
                comps += 1
                st = [i]
                vis[i] = 1
                sz = 0
                while st:
                    c = st.pop()
                    sz += 1
                    for nb in adj[c]:
                        if not vis[nb]:
                            vis[nb] = 1
                            st.append(nb)
                sizes.append(sz)
        sizes.sort(reverse=True)
        print(f"  {mname:15s}: {comps:4d} islands, top 10 sizes={sizes[:10]}, min size={min(sizes) if sizes else 0}")

# Render original untouched source blend front & back with EEVEE
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.23, 1.0)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

for l in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(l, do_unlink=True)

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    obj.rotation_euler = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

# Center of original blend is roughly X=-34, Y=-5, Z=-31
tgt = (-34.0, -5.0, -31.0)
for nm, pos, en in [("Key", (-10, -90, 20), 3.0), ("Fill", (-70, -90, -10), 1.8), ("Rim", (-34, 60, 0), 2.5)]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = en
    scene.collection.objects.link(lo)
    look_at(lo, pos, tgt)

cam = bpy.data.objects.new("SrcCam", bpy.data.cameras.new("SrcCam"))
cam.data.lens = 45.0
scene.collection.objects.link(cam)
scene.camera = cam

# Note: check which way source faces (look from -Y toward +Y and from +Y toward -Y)
look_at(cam, (-34.0, -135.0, -31.0), tgt)
scene.render.filepath = str(SCRATCH_DIR / "src_untouched_front_negY.png")
bpy.ops.render.render(write_still=True)

# Zoom on Cylinder.001 hand (X~-12, Y~-1, Z~-35)
look_at(cam, (-12.0, -32.0, -35.0), (-12.0, -1.0, -35.0))
scene.render.filepath = str(SCRATCH_DIR / "src_hand_R_closeup.png")
bpy.ops.render.render(write_still=True)

# Zoom on Head/Face (around Z=0..-10, X=-34)
look_at(cam, (-34.0, -35.0, -3.0), (-34.0, -2.0, -3.0))
scene.render.filepath = str(SCRATCH_DIR / "src_head_closeup.png")
bpy.ops.render.render(write_still=True)

print("[OK] Source audit complete!")
