import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    lines = [f.readline() for _ in range(406140)]

for l in lines[406085:406140]:
    print(l.rstrip())
