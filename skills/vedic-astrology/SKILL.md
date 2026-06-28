---
name: vedic-astrology
description: Compute authentic Vedic (Jyotish) astrology readings — horoscope life predictions, compatibility/Kuta match reports, Chaldean numerology, planet/house chart data, general chart properties (Lagna, Moon sign, Nakshatra, Tithi, doshas), and Ashtakvarga charts. Use whenever a user asks about their birth chart, kundli, horoscope, marriage compatibility, name numerology, planetary positions, nakshatras, yogas, doshas, or dasha periods. Powered by the VedAstro.org Swiss Ephemeris engine (Raman Ayanamsa).
---

# Vedic Astrology

This skill turns natal birth details into real Vedic astrology calculations by
calling the VedAstro.org API through a bundled, dependency-free Python CLI
(`scripts/vedastro.py`). It is the self-contained form of the VedAstro MCP
server — same six capabilities, no hosted endpoint required.

## When to use

Reach for this skill whenever the request involves Vedic/Jyotish astrology:
birth charts (kundli), horoscope predictions, marriage/relationship
compatibility, numerology of a name or number, planetary positions, houses,
nakshatras, yogas, doshas (e.g. Mangal/Kuja Dosha), or Ashtakvarga.

This skill does **not** invent predictions. It fetches authentic computed data,
which you then interpret and summarize for the user.

## What you need first

Every chart calculation needs five birth parameters. Collect them before
calling (numerology needs only a name):

| Parameter | Format | Example |
|-----------|--------|---------|
| latitude  | decimal degrees | `19.0760` |
| longitude | decimal degrees | `72.8777` |
| birth time | `HH:MM` 24-hour | `14:30` |
| birth date | `DD/MM/YYYY` | `25/10/1992` |
| timezone  | `+HH:MM` / `-HH:MM` | `+05:30` |

If a user gives a city instead of coordinates, look up the lat/long and the
historical timezone offset for that date, confirm with the user if unsure, then
call the tool. All calculations use the **Raman Ayanamsa** system.

## How to run

```bash
python3 scripts/vedastro.py <command> [options] [--pretty]
```

Output is JSON on stdout. Pass `--api-key KEY` (or set `VEDASTRO_API_KEY`) for
unlimited requests; without it the free tier allows ~5 requests/minute, so avoid
firing many calls in a tight loop.

### Commands

**`horoscope`** — full life predictions (personality, career, wealth, marriage,
health, children, longevity, yogas, house placements):
```bash
python3 scripts/vedastro.py horoscope \
  --latitude 19.0760 --longitude 72.8777 \
  --time 14:30 --date 25/10/1992 --timezone +05:30
```

**`match`** — compatibility report with Kuta score % and all 16 Kuta factors:
```bash
python3 scripts/vedastro.py match \
  --male-latitude 28.61 --male-longitude 77.21 \
  --male-time 08:30 --male-date 15/06/1990 --male-timezone +05:30 \
  --female-latitude 34.05 --female-longitude -118.24 \
  --female-time 14:20 --female-date 22/09/1992 --female-timezone -07:00
```

**`numerology`** — Chaldean name-number prediction, ruling planet, life-aspect
scores. Works for people, businesses, projects, house/car numbers:
```bash
python3 scripts/vedastro.py numerology --name "Souvik Dhua"
```

**`raw`** — raw data for all 9 planets and 12 houses (signs, constellations,
lords, degrees, retrograde, aspects). Use for detailed chart analysis:
```bash
python3 scripts/vedastro.py raw \
  --latitude 19.0760 --longitude 72.8777 \
  --time 14:30 --date 25/10/1992 --timezone +05:30
```

**`general`** — 24 chart properties: Lagna, Moon sign, Nakshatra, Sunrise/Sunset,
Nithya Yoga, Karana, Tithi, day/night birth, Varna, Hora, weekday lord, Kuja
Dosa score, Maraka planets, Kartari yoga, Pancha Pakshi bird, and more:
```bash
python3 scripts/vedastro.py general \
  --latitude 19.0760 --longitude 72.8777 \
  --time 14:30 --date 25/10/1992 --timezone +05:30
```

**`ashtakvarga`** — Sarvashtakavarga (combined strength across 12 signs) and
Bhinnashtakavarga (per-planet contributions); used for transit/strength work:
```bash
python3 scripts/vedastro.py ashtakvarga \
  --latitude 19.0760 --longitude 72.8777 \
  --time 14:30 --date 25/10/1992 --timezone +05:30
```

## Interpreting results

The API returns structured data, not prose. Read `references/interpretation.md`
for guidance on turning planet/house/Kuta/Ashtakvarga output into a clear,
well-organized reading for the user. Present findings grouped by life area, lead
with the strongest signals, and note that this is traditional astrology offered
for reflection — not deterministic fact, medical, legal, or financial advice.

## Errors

A non-zero exit prints `{"error": "..."}` to stderr. Common causes: rate
limiting on the free tier (wait and retry), malformed date/time/timezone
formats, or transient network issues. Re-check the parameter formats above
before retrying.
