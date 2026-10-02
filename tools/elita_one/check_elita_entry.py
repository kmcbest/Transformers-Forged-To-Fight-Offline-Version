import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import gamedata
import json

user_data = gamedata.build_user_data()
heroes = user_data.get("updates", {}).get("heroes", [])

elita_hero = next((h for h in heroes if h.get("bid") == "elita_one_gs"), None)
print(f"Elita hero in user_data: {json.dumps(elita_hero, indent=2)}")

login_data = gamedata.build_login_data()
print(f"Elita in login_data['heroes']: {'elita_one_gs' in login_data.get('heroes', {})}")
print(f"Elita in login_data['characters']: {'elita_one_gs' in login_data.get('characters', {})}")
print(f"Elita in login_data['blueprints']: {'elita_one_gs' in login_data.get('blueprints', {})}")
if 'elita_one_gs' in login_data.get('heroes', {}):
    print(f"Hero data: {json.dumps(login_data['heroes']['elita_one_gs'], indent=2)}")
if 'elita_one_gs' in login_data.get('characters', {}):
    print(f"Character data: {json.dumps(login_data['characters']['elita_one_gs'], indent=2)}")
