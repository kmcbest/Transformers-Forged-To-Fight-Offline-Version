import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    in_pc = False
    count = 0
    for line in f:
        if "public class PropsController :" in line:
            in_pc = True
        elif in_pc:
            print(line.rstrip())
            count += 1
            if count > 80:
                break
