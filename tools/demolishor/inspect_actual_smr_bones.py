# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('assets_redeco/demolishor_gs.assetbundle')
go_names = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 80:
            bnames = [go_names.get(tr_to_go.get(b.get('m_PathID'))) for b in bones]
            print(f"SMR PathID {obj.path_id}: {len(bones)} bones")
            print("First 10 bones:", bnames[:10])
            print("Bone 0:", bnames[0])
            print("Bone 10:", bnames[10])
            print("Bone 52:", bnames[52])
            print("Bone 74:", bnames[74])
