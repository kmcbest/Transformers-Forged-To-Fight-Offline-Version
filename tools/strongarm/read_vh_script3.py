import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r'E:\Agent\TFTF-blender\tools\strongarm\build_aligned_strongarm_vh.py', 'r', encoding='utf-8') as f:
    code = f.read()
print('\n'.join(code.splitlines()[160:213]))
