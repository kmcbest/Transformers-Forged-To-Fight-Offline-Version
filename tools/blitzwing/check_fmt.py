import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
from UnityPy.enums import TextureFormat

for fmt in (3, 4, 7, 34, 47):
    try:
        print(f"fmt {fmt} = {TextureFormat(fmt)}")
    except Exception as e:
        print(f"fmt {fmt} = {e}")
