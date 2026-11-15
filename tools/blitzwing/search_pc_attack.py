import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    in_pc = False
    for line in f:
        if "public class PlayerController :" in line:
            in_pc = True
        elif in_pc:
            if "Attack" in line or "Heavy" in line or "EnterMove" in line or "PlayMove" in line:
                print(line.strip())
            if "public class " in line and "PlayerController" not in line:
                break
