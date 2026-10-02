import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import gamedata

for bid in ["necrotronus_gs_kabam", "arcee_gs_deluxe2014", "elita_one_gs", "cheetor_bw_transmetal"]:
    h = gamedata.build_hero_entry(bid)
    print(f"{bid}: class={gamedata.ROSTER.get(bid)}, hp={h.get('max_hp')}, atk={h.get('attack')}, rating={h.get('rating')}")
