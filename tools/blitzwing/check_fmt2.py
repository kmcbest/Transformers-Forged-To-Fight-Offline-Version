import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from UnityPy.enums import TextureFormat

print(TextureFormat(7).name)
print(TextureFormat(4).name)
print(TextureFormat(34).name)
