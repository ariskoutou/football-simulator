import csv
import io
import json
import os
import re
import urllib.request

# Ονόματα ομάδων στο Football-Data CSV -> Όνομα στην εφαρμογή
FD_MAPPING = {
    "Arsenal": "Arsenal", "Aston Villa": "Aston Villa", "Bournemouth": "Bournemouth",
    "Brentford": "Brentford", "Brighton": "Brighton", "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace", "Everton": "Everton", "Fulham": "Fulham",
    "Ipswich": "Ipswich", "Leicester": "Leicester", "Liverpool": "Liverpool",
    "Man City": "Manchester City", "Man United": "Manchester United",
    "Newcastle": "Newcastle United", "Nott'm Forest": "Nottingham Forest",
    "Southampton": "Southampton", "Tottenham": "Tottenham", "West Ham": "West Ham",
    "Wolves": "Wolverhampton Wanderers",
    "Atalanta": "Atalanta", "Bologna": "Bologna", "Cagliari": "Cagliari",
    "Como": "Como", "Empoli": "Empoli", "Fiorentina": "Fiorentina",
    "Genoa": "Genoa", "Verona": "Hellas Verona", "Inter": "Inter",
    "Juventus": "Juventus", "Lazio": "Lazio", "Lecce": "Lecce",
    "Monza": "Monza", "Napoli": "Napoli", "Parma": "Parma",
    "Roma": "Roma", "Torino": "Torino", "Udinese": "Udinese",
    "Venezia": "Venezia", "Milan": "AC Milan"
}

# Αντιστοίχιση ονόματος Understat -> Όνομα στην εφαρμογή
UNDERSTAT_TEAMS = {
    "Chelsea": "Chelsea",
    "Manchester_United": "Manchester United",
    "Arsenal": "Arsenal",
    "Liverpool": "Liverpool",
    "Manchester_City": "Manchester City",
    "Tottenham": "Tottenham",
    "Aston_Villa": "Aston Villa",
    "Newcastle_United": "Newcastle United",
    "Brighton": "Brighton",
    "Fulham": "Fulham",
    "Brentford": "Brentford",
    "Bournemouth": "Bournemouth",
    "Everton": "Everton",
    "West_Ham": "West Ham",
    "Leicester": "Leicester",
    "Nottingham_Forest": "Nottingham Forest",
    "Ipswich": "Ipswich",
    "Southampton": "Southampton",
    "Wolverhampton_Wanderers": "Wolverhampton Wanderers"
}

CSV_URLS = [
    "https://www.football-data.co.uk/mmz4281/2627/E0.csv",
    "https://www.football-data.co.uk/mmz4281/2627/I1.csv"
]

def get_official_xg():
    xg_data = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for u_slug, app_name in UNDERSTAT_TEAMS.items():
        url = f"https://understat.com/team/{u_slug}"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8')

            match = re.search(r"datesData\s*=\s*JSON\.parse\('([^']+)'\)", html)
            if not match:
                continue

            hex_data = match.group(1)
            raw_json = bytes.fromhex(hex_data).decode('utf-8')
            matches = json.loads(raw_json)

            # Φιλτράρισμα ολοκληρωμένων αγώνων της τρέχουσας σεζόν
            h_xg = [float(m['xG']) for m in matches if m.get('isResult') and m.get('side') == 'h' and m.get('datetime', '') >= '2026-08-01']
            a_xg = [float(m['xG']) for m in matches if m.get('isResult') and m.get('side') == 'a' and m.get('datetime', '') >= '2026-08-01']

            xg_data[app_name] = {
                'home_xg': round(sum(h_xg) / len(h_xg), 2) if h_xg else None,
                'away_xg': round(sum(a_xg) / len(a_xg), 2) if a_xg else None
            }
        except Exception:
            pass
    return xg_data

def update_all_stats():
    # 1. Λήψη πραγματικών xG από Understat
    official_xg = get_official_xg()

    # 2. Λήψη Shots, SoT, Corners, Cards από Football-Data CSV
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
                        hs, hst, hc = float(row.get('HS', 0)), float(row.get('HST', 0)), float(row.get('HC', 0))
                        h_card = float(row.get('HY', 0)) + float(row.get('HR', 0))

                        as_, ast, ac = float(row.get('AS', 0)), float(row.get('AST', 0)), float(row.get('AC', 0))
                        a_card = float(row.get('AY', 0)) + float(row.get('AR', 0))
                    except ValueError:
                        continue

                    app_h = FD_MAPPING.get(h_team, h_team)
                    app_a = FD_MAPPING.get(a_team, a_team)

                    if app_h not in team_data:
                        team_data[app_h] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[app_h]['home']['s'].append(hs)
                    team_data[app_h]['home']['st'].append(hst)
                    team_data[app_h]['home']['c'].append(hc)
                    team_data[app_h]['home']['cd'].append(h_card)

                    if app_a not in team_data:
                        team_data[app_a] = {'home': {'s': [], 'st': [], 'c': [], 'cd': []}, 'away': {'s': [], 'st': [], 'c': [], 'cd': []}}
                    team_data[app_a]['away']['s'].append(as_)
                    team_data[app_a]['away']['st'].append(ast)
                    team_data[app_a]['away']['c'].append(ac)
                    team_data[app_a]['away']['cd'].append(a_card)
        except Exception as e:
            print(f"Σφάλμα CSV: {e}")

    result_json = {}

    def avg(lst, fallback):
        return round(sum(lst) / len(lst), 2) if lst else fallback

    for team, sides in team_data.items():
        h_shots = avg(sides['home']['s'], 12.0)
        h_sot = avg(sides['home']['st'], 4.5)
        a_shots = avg(sides['away']['s'], 10.5)
        a_sot = avg(sides['away']['st'], 3.8)

        # Αν βρέθηκε επίσημο xG από Understat, χρησιμοποιείται αυτό.
        # Αν όχι, υπολογίζεται ποδοσφαιρικά από τα SoT.
        real_xg = official_xg.get(team, {})
        home_xg = real_xg.get('home_xg') or round(h_sot * 0.27 + (h_shots - h_sot) * 0.02, 2)
        away_xg = real_xg.get('away_xg') or round(a_sot * 0.22 + (a_shots - a_sot) * 0.015, 2)

        result_json[team] = {
            "home": {
                "xg": home_xg,
                "shots": h_shots,
                "sot": h_sot,
                "corners": avg(sides['home']['c'], 5.0),
                "cards": avg(sides['home']['cd'], 2.0)
            },
            "away": {
                "xg": away_xg,
                "shots": a_shots,
                "sot": a_sot,
                "corners": avg(sides['away']['c'], 4.2),
                "cards": avg(sides['away']['cd'], 2.2)
            }
        }

    with open('teams_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("Επιτυχής ενημέρωση με επίσημα xG και στατιστικά!")

if __name__ == '__main__':
    update_all_stats()
