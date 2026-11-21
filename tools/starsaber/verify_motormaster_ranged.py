import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

proc_path = r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle"
moves_path = r"E:\Agent\TFTF\assets_netflix\moves.assetbundle"

env_proc = UnityPy.load(proc_path)
proc_pids = {}
for obj in env_proc.objects:
    if obj.type.name == 'AnimationClip':
        tree = obj.read_typetree()
        proc_pids[obj.path_id] = tree.get('m_Name', '')

target_clip_pids = [-3948795660449728024, 6078334979657561662, 8599663582438923052]
for cpid in target_clip_pids:
    print(f"Clip {cpid}: {proc_pids.get(cpid, 'NOT FOUND')}")

env_moves = UnityPy.load(moves_path)
moves_pids = {}
for obj in env_moves.objects:
    if obj.type.name in ('MonoBehaviour', 'GameObject'):
        tree = obj.read_typetree()
        name = tree.get('m_Name', '')
        if name:
            moves_pids[obj.path_id] = name

target_move_pids = [6811001981586741581, 4776763212269214863, -4795991277224341066]
for mpid in target_move_pids:
    print(f"Move {mpid}: {moves_pids.get(mpid, 'NOT FOUND')}")
