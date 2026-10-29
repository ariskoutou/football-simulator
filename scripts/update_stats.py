import json
import os
import urllib.request
import re

LEAGUES = {
    'Serie_A': 'Serie A',
    'EPL': 'Premier League',
    'La_Liga': 'La Liga'
}

def get_understat_team_stats(team_name):
    url = f"https://understat.com/team/{urllib.request.quote(team_name)}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8')
            
        match = re.search(r"datesData\s*=\s*JSON\.parse\('([^']+)'\)", html)
        if not match:
            return None
            
        hex_data = match.group(1)
        json_str = bytes.fromhex(hex_data).decode('utf-8')
        matches = json.loads(json_str)
        
        home_matches = [m for m in matches if m.get('side') == 'h' and m.get('isResult')]
        away_matches = [m for m in matches if m.get('side') == 'a' and m.get('isResult')]
        
        def calc_averages(match_list):
            if not match_list:
                return {"xg": 1.40, "shots": 13.0, "sot": 4.5, "corners": 5.0, "cards": 2.0}
            n = len(match_list)
            sum_xg = sum(float(m.get('xG', 0)) for m in match_list)
            sum_shots = sum(float(m.get('shots', 0)) for m in match_list)
            sum_sot = sum(float(m.get('shotsOnTarget', 0)) for m in match_list)
            
            return {
                "xg": round(sum_xg / n, 2),
                "shots": round(sum_shots / n, 1),
                "sot": round(sum_sot / n, 1),
                "corners": round(5.2, 1),
                "cards": round(2.0, 1)
            }
            
        return {
            "home": calc_averages(home_matches),
            "away": calc_averages(away_matches)
        }
    except Exception as e:
        print(f"Error fetching stats for {team_name}: {e}")
        return None

def main():
    json_path = 'teams_stats.json'
    existing_data = {}
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = {}

    teams_to_update = list(existing_data.keys())
    if not teams_to_update:
        teams_to_update = [
            "Fiorentina", "Atalanta", "Inter", "Juventus", "AC Milan", 
            "Napoli", "Roma", "Lazio", "Chelsea", "Manchester United",
            "Paris Saint Germain", "Lyon", "Real Madrid", "Barcelona"
        ]

    for team in teams_to_update:
        print(f"Updating {team}...")
        stats = get_understat_team_stats(team)
        if stats:
            corners_h = existing_data.get(team, {}).get('home', {}).get('corners', 5.5)
            corners_a = existing_data.get(team, {}).get('away', {}).get('corners', 4.2)
            cards_h = existing_data.get(team, {}).get('home', {}).get('cards', 2.0)
            cards_a = existing_data.get(team, {}).get('away', {}).get('cards', 2.2)
            
            stats['home']['corners'] = corners_h
            stats['away']['corners'] = corners_a
            stats['home']['cards'] = cards_h
            stats['away']['cards'] = cards_a
            
            existing_data[team] = stats

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    print("teams_stats.json updated successfully!")

if __name__ == '__main__':
    main()
