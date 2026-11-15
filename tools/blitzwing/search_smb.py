import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

with open(r"E:\Agent\TFTF\il2cpp_dump\dump.cs", "r", encoding="utf-8") as f:
    in_smb = False
    for line in f:
        if "public class MoveStateMachineBehaviour :" in line:
            in_smb = True
        elif in_smb:
            print(line.rstrip())
            if "public class " in line:
                break
