import csv
import io
import json
import os
import urllib.request

FD_MAPPING = {
    # Premier League
    "Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Brighton": "Brighton", "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace", "Everton": "Everton", "Fulham": "Fulham",
    "Ipswich": "Ipswich", "Leicester": "Leicester", "Liverpool": "Liverpool",
    "Man City": "Manchester City", "Man United": "Manchester United",
    "Newcastle": "Newcastle United", "Nott'm Forest": "Nottingham Forest",
    "Southampton": "Southampton", "Tottenham": "Tottenham", "West Ham": "West Ham",
    "Wolves": "Wolverhampton Wanderers",
    # Serie A
    "Atalanta": "Atalanta", "Bologna": "Bologna", "Cagliari": "Cagliari",
    "Como": "Como", "Empoli": "Empoli", "Fiorentina": "Fiorentina",
    "Genoa": "Genoa", "Verona": "Hellas Verona", "Inter": "Inter",
    "Juventus": "Juventus", "Lazio": "Lazio", "Lecce": "Lecce",
    "Monza": "Monza", "Napoli": "Napoli", "Parma": "Parma",
    "Roma": "Roma", "Torino": "Torino", "Udinese": "Udinese",
    "Venezia": "Venezia", "Milan": "AC Milan"
}

CSV_URLS = [
    "https://www.football-data.co.uk/mmz4281/2627/E0.csv",  # Premier League 2026-2027
    "https://www.football-data.co.uk/mmz4281/2627/I1.csv"   # Serie A 2026-2027
]

def update_all_stats():
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
                        hs = float(row.get('HS', 0) or 0)
                        hst = float(row.get('HST', 0) or 0)
                        hc = float(row.get('HC', 0) or 0)
                        hy = float(row.get('HY', 0) or 0) + float(row.get('HR', 0) or 0)

                        as_ = float(row.get('AS', 0) or 0)
                        ast = float(row.get('AST', 0) or 0)
                        ac = float(row.get('AC', 0) or 0)
                        ay = float(row.get('AY', 0) or 0) + float(row.get('AR', 0) or 0)
                    except ValueError:
                        continue

                    app_h = FD_MAPPING.get(h_team, h_team)
                    app_a = FD_MAPPING.get(a_team, a_team)

                    if app_h not in team_data:
                        team_data[app_h] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[app_h]['home']['s'].append(hs)
                    team_data[app_h]['home']['st'].append(hst)
                    team_data[app_h]['home']['c'].append(hc)
                    team_data[app_h]['home']['cd'].append(hy)

                    if app_a not in team_data:
                        team_data[app_a] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[app_a]['away']['s'].append(as_)
                    team_data[app_a]['away']['st'].append(ast)
                    team_data[app_a]['away']['c'].append(ac)
                    team_data[app_a]['away']['cd'].append(ay)
        except Exception as e:
            print(f"Σφάλμα ανάγνωσης CSV ({url}): {e}")

    result_json = {}

    def avg(lst, fallback):
        return round(sum(lst) / len(lst), 2) if lst else fallback

    for team, sides in team_data.items():
        result_json[team] = {
            "home": {
                "shots": avg(sides['home']['s'], 12.0),
                "sot": avg(sides['home']['st'], 4.5),
                "corners": avg(sides['home']['c'], 5.0),
                "cards": avg(sides['home']['cd'], 2.0)
            },
            "away": {
                "shots": avg(sides['away']['s'], 10.5),
                "sot": avg(sides['away']['st'], 3.8),
                "corners": avg(sides['away']['c'], 4.2),
                "cards": avg(sides['away']['cd'], 2.2)
            }
        }

    with open('teams_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("Το teams_stats.json ενημερώθηκε χωρίς xG!")

if __name__ == '__main__':
    update_all_stats()
