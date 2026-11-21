import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

moves_path = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
if not moves_path.exists():
    moves_path = Path(r"E:\Agent\TFTF\assets_netflix\moves.assetbundle")

env = UnityPy.load(str(moves_path))
moves = [obj for obj in env.objects if obj.type.name == "TextAsset"]
print(f"Total TextAssets in {moves_path}: {len(moves)}")

# Check Chromia and Dead End
chromia = [obj.read_typetree().get('m_Name') for obj in moves if 'chromia' in (obj.read_typetree().get('m_Name') or '').lower()]
deadend = [obj.read_typetree().get('m_Name') for obj in moves if 'deadend' in (obj.read_typetree().get('m_Name') or '').lower() or 'dead_end' in (obj.read_typetree().get('m_Name') or '').lower()]
lifeline = [obj.read_typetree().get('m_Name') for obj in moves if 'lifeline' in (obj.read_typetree().get('m_Name') or '').lower()]

print(f"Chromia moves: {len(chromia)}")
print(f"Dead End moves: {len(deadend)}")
print(f"Lifeline moves: {len(lifeline)}")
