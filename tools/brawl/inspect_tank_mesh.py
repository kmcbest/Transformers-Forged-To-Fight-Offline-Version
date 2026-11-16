import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

vh_mesh = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx")
if vh_mesh:
    verts = [vh_mesh.matrix_world @ v.co for v in vh_mesh.data.vertices]
    verts = np.array([[v.x, v.y, v.z] for v in verts])
    print(f"Tank World Bounds:")
    print(f"  X: [{verts[:,0].min():.4f}, {verts[:,0].max():.4f}] (center={(verts[:,0].min()+verts[:,0].max())/2:.4f}, span={verts[:,0].max()-verts[:,0].min():.4f})")
    print(f"  Y: [{verts[:,1].min():.4f}, {verts[:,1].max():.4f}] (center={(verts[:,1].min()+verts[:,1].max())/2:.4f}, span={verts[:,1].max()-verts[:,1].min():.4f})")
    print(f"  Z: [{verts[:,2].min():.4f}, {verts[:,2].max():.4f}] (center={(verts[:,2].min()+verts[:,2].max())/2:.4f}, span={verts[:,2].max()-verts[:,2].min():.4f})")

    # Check which axis the cannon barrel extends along
    # Cannon barrel should be at high Z and extend far along one axis
    high_z = verts[verts[:, 2] > (verts[:, 2].max() - 0.5)]
    print(f"High Z vertices count: {len(high_z)}")
    print(f"  High Z X span: [{high_z[:,0].min():.4f}, {high_z[:,0].max():.4f}]")
    print(f"  High Z Y span: [{high_z[:,1].min():.4f}, {high_z[:,1].max():.4f}]")

# Also check Megatron tank OBJ bounds
with open(r'E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\cha_megatron_cin_rotf_01_tank.obj', 'r') as f:
    m_verts = []
    for line in f:
        if line.startswith('v '):
            p = line.strip().split()
            m_verts.append([float(p[1]), float(p[2]), float(p[3])])
    m_verts = np.array(m_verts)
    print("\nMegatron Tank OBJ Bounds:")
    print(f"  X: [{m_verts[:,0].min():.4f}, {m_verts[:,0].max():.4f}] (center={(m_verts[:,0].min()+m_verts[:,0].max())/2:.4f}, span={m_verts[:,0].max()-m_verts[:,0].min():.4f})")
    print(f"  Y: [{m_verts[:,1].min():.4f}, {m_verts[:,1].max():.4f}] (center={(m_verts[:,1].min()+m_verts[:,1].max())/2:.4f}, span={m_verts[:,1].max()-m_verts[:,1].min():.4f})")
    print(f"  Z: [{m_verts[:,2].min():.4f}, {m_verts[:,2].max():.4f}] (center={(m_verts[:,2].min()+m_verts[:,2].max())/2:.4f}, span={m_verts[:,2].max()-m_verts[:,2].min():.4f})")
