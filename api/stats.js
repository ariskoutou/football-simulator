export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { team, venue } = req.query; // venue: 'home' ή 'away'
  if (!team) {
    return res.status(400).json({ error: "Missing team parameter" });
  }

  const isHome = (venue || 'home').toLowerCase() === 'home';

  try {
    // 1. Scraping / Fetching Understat data για xG
    const understatUrl = `https://understat.com/team/${encodeURIComponent(team)}/2026`;
    const understatRes = await fetch(understatUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    let xg = isHome ? 1.55 : 1.15;
    let shots = isHome ? 14.5 : 11.0;
    let sot = isHome ? 5.2 : 3.6;
    let corners = isHome ? 5.5 : 4.2;
    let cards = isHome ? 2.0 : 2.2;

    if (understatRes.ok) {
      const html = await understatRes.text();
      // Το Understat αποθηκεύει τα δεδομένα των αγώνων σε JSON μέσα σε script tag
      const matchesDataMatch = html.match(/datesData\s*=\s*JSON\.parse\('([^']+)'\)/);
      if (matchesDataMatch && matchesDataMatch[1]) {
        const decoded = Buffer.from(matchesDataMatch[1], 'hex').toString('utf8');
        const matches = JSON.parse(decoded);

        const filtered = matches.filter(m => m.side === (isHome ? 'h' : 'a') && m.isResult);
        if (filtered.length > 0) {
          const sumXg = filtered.reduce((acc, m) => acc + parseFloat(m.xG || 0), 0);
          const sumShots = filtered.reduce((acc, m) => acc + parseFloat(m.shots || 0), 0);
          const sumSot = filtered.reduce((acc, m) => acc + parseFloat(m.shotsOnTarget || 0), 0);

          xg = Number((sumXg / filtered.length).toFixed(2));
          shots = Number((sumShots / filtered.length).toFixed(1));
          sot = Number((sumSot / filtered.length).toFixed(1));
        }
      }
    }

    return res.status(200).json({
      team,
      venue: isHome ? 'Home' : 'Away',
      xg,
      shots,
      sot,
      corners,
      cards
    });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
