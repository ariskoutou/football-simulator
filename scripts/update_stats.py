import csv
import io
import json
import os
import re
import urllib.request
from datetime import datetime

# Ορισμός τρέχουσας σεζόν
# Για τη σεζόν που ξεκινά το καλοκαίρι (π.χ. 2024-2025 -> 2024, 2025-2026 -> 2025 κ.ο.κ.)
CURRENT_SEASON_START_YEAR = "2024" 
SEASON_CUTOFF_DATE = f"{CURRENT_SEASON_START_YEAR}-08-01"

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
    "https://www.football-data.co.uk/mmz4281/2425/E0.csv",  # Premier League (μόνο πρωτάθλημα)
    "https://www.football-data.co.uk/mmz4281/2425/I1.csv"   # Serie A (μόνο πρωτάθλημα)
]

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
            print(f"Σφάλμα CSV ({url}): {e}")

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
    # Κλήση απευθείας στο endpoint της τρέχουσας σεζόν
    url = f"https://understat.com/team/{urllib.request.quote(team_name)}/{CURRENT_SEASON_START_YEAR}"
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
        
        # Φιλτράρισμα:
        # 1. Μόνο αγώνες που έχουν λήξει (isResult == True)
        # 2. Μόνο αγώνες της φετινής περιόδου (από Αύγουστο και μετά)
        home_matches = [
            m for m in matches 
            if m.get('side') == 'h' 
            and m.get('isResult') == True 
            and m.get('datetime', '') >= SEASON_CUTOFF_DATE
        ]
        
        away_matches = [
            m for m in matches 
            if m.get('side') == 'a' 
            and m.get('isResult') == True 
            and m.get('datetime', '') >= SEASON_CUTOFF_DATE
        ]
        
        def calc_averages(match_list):
            if not match_list:
                return {"xg": 1.40, "shots": 13.0, "sot": 4.5}
            n = len(match_list)
            sum_xg = sum(float(m.get('xG',
