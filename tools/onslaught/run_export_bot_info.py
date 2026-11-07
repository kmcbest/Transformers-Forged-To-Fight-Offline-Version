import sys
from pathlib import Path

# Add Server directory to sys.path
server_dir = Path(r"E:\Agent\TFTF-blender\Server")
sys.path.insert(0, str(server_dir))

import gamedata
gamedata.export_bot_info_header()
print("[OK] Regenerated bot_info.h!")
