import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

moves_path = r"E:\Agent\TFTF\assets_netflix\moves.assetbundle"
env = UnityPy.load(moves_path)
for obj in env.objects:
    if obj.type.name == 'TextAsset':
        tree = obj.read_typetree()
        name = tree.get('m_Name', '')
        if 'handgun_left_xl' in name.lower():
            print(f"{obj.path_id}: {name}")
