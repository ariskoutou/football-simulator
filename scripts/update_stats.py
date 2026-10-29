import csv
import io
import json
import os
import re
import urllib.request

TARGET_SEASON = "2026"

FD_TEAM_MAPPING = {
    # Premier League
    "Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Brighton": "Brighton", "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace", "Everton": "Everton", "Fulham": "Fulham",
    "Ipswich": "Ipswich", "Leicester": "Leicester", "Liverpool": "Liverpool",
    "Manchester City": "Man City", "Manchester United": "Man United",
    "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest",
    "Southampton": "Southampton", "Tottenham": "Tottenham", "West Ham": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    # Serie A
    "Atalanta": "Atalanta", "Bologna": "Bologna", "Cagliari": "Cagliari",
    "Como": "Como", "Empoli": "Empoli", "Fiorentina": "Fiorentina",
    "Genoa": "Genoa", "Hellas Verona": "Verona", "Inter": "Inter",
    "Juventus": "Juventus", "Lazio": "Lazio", "Lecce": "Lecce",
    "Monza": "Monza", "Napoli": "Napoli", "Parma": "Parma",
    "Roma": "Roma", "Torino": "Torino", "Udinese": "Udinese",
    "Venezia": "Venezia", "AC Milan": "Milan"
}

CSV_URLS = [
    "https://www.football-data.co.uk/mmz4281/2627/E0.csv",  # Premier League 2026-2027
    "https://www.football-data.co.uk/mmz4281/2627/I1.csv"   # Serie A 2026-2027]

def fetch_corners_and_cards():
    team_data = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in CSV_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    h_team = row.get('HomeTeam')
                    a_team = row.get('AwayTeam')
                    if not h_team or not a_team:
                        continue

                    try:
                        hc = float(row.get('HC', 0) or 0)
                        ac = float(row.get('AC', 0) or 0)
                        hy = float(row.get('HY', 0) or 0) + float(row.get('HR', 0) or 0)
                        ay = float(row.get('AY', 0) or 0) + float(row.get('AR', 0) or 0)
                    except ValueError:
                        continue

                    if h_team not in team_data:
                        team_data[h_team] = {'home': {'c': [], 'cd': []}, 'away': {'c': [], 'cd': []}}
                    team_data[h_team]['home']['c'].append(hc)
                    team_data[h_team]['home']['cd'].append(hy)

                    if a_team not in team_data:
                        team_data[a_team] = {'home': {'c': [], 'cd': []}, 'away': {'c': [], 'cd': []}}
                    team_data[a_team]['away']['c'].append(ac)
                    team_data[a_team]['away']['cd'].append(ay)
        except Exception as e:
            pass

    averages = {}
    for team, sides in team_data.items():
        averages[team] = {
            'home': {
                'corners': round(sum(sides['home']['c']) / len(sides['home']['c']), 2) if sides['home']['c'] else 5.2,
                'cards': round(sum(sides['home']['cd']) / len(sides['home']['cd']), 2) if sides['home']['cd'] else 2.0
            },
            'away': {
                'corners': round(sum(sides['away']['c']) / len(sides['away']['c']), 2) if sides['away']['c'] else 4.2,
                'cards': round(sum(sides['away']['cd']) / len(sides['away']['cd']), 2) if sides['away']['cd'] else 2.2
            }
        }
    return averages

def get_understat_team_stats(team_name):
    url = f"https://understat.com/team/{urllib.request.quote(team_name)}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
        
        # Κρατάμε τα ολοκληρωμένα ματς
        # Ταξινομούμε ανά ημερομηνία για να πάρουμε τα πιο πρόσφατα
        finished = [m for m in matches if m.get('isResult') == True]
        
        # Αν υπάρχουν ματς με ημερομηνία πρόσφατη (τρέχουσα περίοδος)
        # Κρατάμε μόνο αυτά
        recent_matches = [m for m in finished if m.get('datetime', '') >= '2024-08-01']
        if not recent_matches:
            recent_matches = finished[-15:] # fallback στα τελευταία ματς
            
        home_matches = [m for m in recent_matches if m.get('side') == 'h']
        away_matches = [m for m in recent_matches if m.get('side') == 'a']
        
        def calc_averages(match_list):
            if not match_list:
                return {"xg": 1.40, "shots": 12.0, "sot": 4.5}
            n = len(match_list)
            sum_xg = sum(float(m.get('xG', 0)) for m in match_list)
            sum_shots = sum(float(m.get('shots', 0)) for m in match_list)
            sum_sot = sum(float(m.get('shotsOnTarget', 0)) for m in match_list)
            
            return {
                "xg": round(sum_xg / n, 2),
                "shots": round(sum_shots / n, 2),
                "sot": round(sum_sot / n, 2)
            }
            
        return {
            "home": calc_averages(home_matches),
            "away": calc_averages(away_matches)
        }
    except Exception as e:
        print(f"Error fetching {team_name}: {e}")
        return None

def main():
    fd_data = fetch_corners_and_cards()

    json_path = 'teams_stats.json'
    existing_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = {}

    teams_to_update = list(FD_TEAM_MAPPING.keys())

    for team in teams_to_update:
        u_stats = get_understat_team_stats(team)
        fd_name = FD_TEAM_MAPPING.get(team, team)
        team_fd = fd_data.get(fd_name, {
            'home': {'corners': 5.5, 'cards': 2.0},
            'away': {'corners': 4.2, 'cards': 2.2}
        })

        if u_stats:
            existing_data[team] = {
                "home": {
                    "xg": u_stats["home"]["xg"],
                    "shots": u_stats["home"]["shots"],
                    "sot": u_stats["home"]["sot"],
                    "corners": team_fd["home"]["corners"],
                    "cards": team_fd["home"]["cards"]
                },
                "away": {
                    "xg": u_stats["away"]["xg"],
                    "shots": u_stats["away"]["shots"],
                    "sot": u_stats["away"]["sot"],
                    "corners": team_fd["away"]["corners"],
                    "cards": team_fd["away"]["cards"]
                }
            }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()
