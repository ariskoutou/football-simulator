import csv
import io
import json
import os
import re
import urllib.request

# Ονόματα Football-Data CSV -> Όνομα στην εφαρμογή
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

# Slugs ομάδων για το Understat
UNDERSTAT_SLUGS = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston_Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal_Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Ipswich": "Ipswich",
    "Leicester": "Leicester",
    "Liverpool": "Liverpool",
    "Manchester City": "Manchester_City",
    "Manchester United": "Manchester_United",
    "Newcastle United": "Newcastle_United",
    "Nottingham Forest": "Nottingham_Forest",
    "Southampton": "Southampton",
    "Tottenham": "Tottenham",
    "West Ham": "West_Ham",
    "Wolverhampton Wanderers": "Wolverhampton_Wanderers"
}

CSV_URLS = [
    "https://www.football-data.co.uk/mmz4281/2627/E0.csv",  # Premier League 2026-2027
    "https://www.football-data.co.uk/mmz4281/2627/I1.csv"   # Serie A 2026-2027
]

def fetch_understat_xg(app_team_name):
    """
    Αντλεί αποκλειστικά το πραγματικό xG από το Understat για εντός και εκτός έδρας αγώνες.
    """
    slug = UNDERSTAT_SLUGS.get(app_team_name)
    if not slug:
        return None, None

    url = f"https://understat.com/team/{slug}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8')

        match = re.search(r"datesData\s*=\s*JSON\.parse\('([^']+)'\)", html)
        if not match:
            return None, None

        hex_data = match.group(1)
        matches = json.loads(bytes.fromhex(hex_data).decode('utf-8'))

        # Φιλτράρισμα ολοκληρωμένων αγώνων από τον Αύγουστο του 2026
        h_xg = [float(m['xG']) for m in matches if m.get('isResult') and m.get('side') == 'h' and m.get('datetime', '') >= '2026-08-01']
        a_xg = [float(m['xG']) for m in matches if m.get('isResult') and m.get('side') == 'a' and m.get('datetime', '') >= '2026-08-01']

        home_avg = round(sum(h_xg) / len(h_xg), 2) if h_xg else None
        away_avg = round(sum(a_xg) / len(a_xg), 2) if a_xg else None

        print(f"[Understat xG] {app_team_name} -> Home: {home_avg} ({len(h_xg)} αγώνες), Away: {away_avg} ({len(a_xg)} αγώνες)")
        return home_avg, away_avg
    except Exception as e:
        print(f"[Understat Warning] Αποτυχία για {app_team_name}: {e}")
        return None, None

def update_all_stats():
    team_data = {}
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 1. Συλλογή Σουτ, SoT, Κόρνερ, Καρτών από Football-Data CSV
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
            print(f"Σφάλμα CSV ({url}): {e}")

    result_json = {}

    def avg(lst, fallback):
        return round(sum(lst) / len(lst), 2) if lst else fallback

    # 2. Ενοποίηση με τα πραγματικά xG από Understat
    for team, sides in team_data.items():
        h_shots = avg(sides['home']['s'], 12.0)
        h_sot = avg(sides['home']['st'], 4.5)
        a_shots = avg(sides['away']['s'], 10.5)
        a_sot = avg(sides['away']['st'], 3.8)

        # Κλήση της ειδικής συνάρτησης για xG
        u_home_xg, u_away_xg = fetch_understat_xg(team)

        # Fallback μόνο αν το Understat είναι offline για τη συγκεκριμένη ομάδα
        final_home_xg = u_home_xg if u_home_xg is not None else round(h_sot * 0.27 + (h_shots - h_sot) * 0.02, 2)
        final_away_xg = u_away_xg if u_away_xg is not None else round(a_sot * 0.22 + (a_shots - a_sot) * 0.015, 2)

        result_json[team] = {
            "home": {
                "xg": final_home_xg,
                "shots": h_shots,
                "sot": h_sot,
                "corners": avg(sides['home']['c'], 5.0),
                "cards": avg(sides['home']['cd'], 2.0)
            },
            "away": {
                "xg": final_away_xg,
                "shots": a_shots,
                "sot": a_sot,
                "corners": avg(sides['away']['c'], 4.2),
                "cards": avg(sides['away']['cd'], 2.2)
            }
        }

    with open('teams_stats.json', 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("Η ενημέρωση ολοκληρώθηκε επιτυχώς!")

if __name__ == '__main__':
    update_all_stats()
