import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    in_prop = False
    for line in f:
        if "public class Prop " in line or "public struct Prop " in line:
            in_prop = True
        elif in_prop:
            print(line.rstrip())
            if "}" in line and len(line.strip()) == 1:
                break
