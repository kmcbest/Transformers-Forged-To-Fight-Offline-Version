import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    in_pd = False
    count = 0
    for line in f:
        if "public class PropData" in line:
            in_pd = True
        elif in_pd:
            print(line.rstrip())
            count += 1
            if count > 80:
                break
