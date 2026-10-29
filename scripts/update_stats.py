import csv
import io
import json
import os
import urllib.request

# Ονόματα ομάδων όπως εμφανίζονται στα επίσημα CSV
# (Premier League & Serie A)
TEAMS = [
    # Premier League
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton", 
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich", 
    "Leicester", "Liverpool", "Man City", "Man United", "Newcastle", 
    "Nott'm Forest", "Southampton", "Tottenham", "West Ham", "Wolves",
    # Serie A
    "Atalanta", "Bologna", "Cagliari", "Como", "Empoli", 
    "Fiorentina", "Genoa", "Verona", "Inter", "Juventus", 
    "Lazio", "Lecce", "Monza", "Napoli", "Parma", 
    "Roma", "Torino", "Udinese", "Venezia", "Milan"
]

# Αντιστοίχιση ονομάτων για το Frontend σου
DISPLAY_NAMES = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "Verona": "Hellas Verona",
    "Milan": "AC Milan"
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
                        # Σουτ, Σουτ στον Στόχο, Κόρνερ, Κάρτες από το επίσημο φύλλο αγώνα
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

                    # Εντός έδρας στατιστικά
                    if h_team not in team_data:
                        team_data[h_team] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[h_team]['home']['s'].append(hs)
                    team_data[h_team]['home']['st'].append(hst)
                    team_data[h_team]['home']['c'].append(hc)
                    team_data[h_team]['home']['cd'].append(hy)

                    # Εκτός έδρας στατιστικά
                    if a_team not in team_data:
                        team_data[a_team] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[a_team]['away']['s'].append(as_)
                    team_data[a_team]['away']['st'].append(ast)
                    team_data[a_team]['away']['c'].append(ac)
                    team_data[a_team]['away']['cd'].append(ay)
        except Exception as e:
            print(f"Σφάλμα ανάγνωσης CSV ({url}): {e}")

    result_json = {}

    for fd_team, metrics in team_data.items():
        # Υπολογισμός πραγματικών μέσων όρων
        def avg(lst, fallback):
            return round(sum(lst) / len(lst), 2) if lst else fallback

        home_shots = avg(metrics['home']['s'], 12.0)
        home_sot = avg(metrics['home']['st'], 4.5)
        home_corners = avg(metrics['home']['c'], 5.2)
        home_cards = avg(metrics['home']['cd'], 2.0)

        away_shots = avg(metrics['away']['s'], 10.5)
        away_sot = avg(metrics['away']['st'], 3.8)
        away_corners = avg(metrics['away']['c'], 4.2)
        away_cards = avg(metrics['away']['cd'], 2.2)

        # Εμφανιζόμενο όνομα στην εφαρμογή
        app_team_name = DISPLAY_NAMES.get(fd_team, fd_team)

        # Υπολογισμός αξιόπιστου xG βάσει SoT και shots (0.10 ανά σουτ + 0.22 ανά SoT bonus)
        home_xg = round(home_shots * 0.08 + home_sot * 0.15, 2)
        away_xg = round(away_shots * 0.08 + away_sot * 0.15, 2)

        result_json[app_team_name] = {
            "home": {
                "xg": home_xg,
                "shots": home_shots,
                "sot": home_sot,
                "corners": home_corners,
                "cards": home_cards
            },
            "away": {
                "xg": away_xg,
                "shots": away_shots,
                "sot": away_sot,
                "corners": away_corners,
                "cards": away_cards
            }
        }

    with open('teams_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("Το teams_stats.json ανανεώθηκε με τα πραγματικά νούμερα του πρωταθλήματος!")

if __name__ == '__main__':
    update_all_stats()
