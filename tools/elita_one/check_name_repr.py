import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import gamedata

name = gamedata.display_name("elita_one_gs", lang="zh")
print("display_name repr:", repr(name))
print("display_name bytes:", name.encode("utf-8"))
