# Vedic Astrology — Skill edition

This directory is the **sublimated** form of the VedAstro MCP server: the full
functionality of the hosted app, re-packaged as a portable [Agent
Skill](https://www.anthropic.com/news/skills). Instead of standing up an Azure
Function and connecting an MCP client over HTTP, an agent reads `SKILL.md` and
calls a single dependency-free Python CLI (`scripts/vedastro.py`) that talks to
the same VedAstro.org API.

Same engine, same Raman Ayanamsa calculations, same six capabilities — no server
to deploy, no connector to configure.

## Capability parity with the MCP server

| MCP tool (`src/functions/mcp.ts`) | Skill command | API endpoint(s) |
|-----------------------------------|---------------|-----------------|
| `get_horoscope_predictions` | `horoscope` | `Calculate/HoroscopePredictions` |
| `get_match_report` | `match` | `Calculate/MatchReport` |
| `get_numerology_prediction` | `numerology` | `Calculate/NameNumberPrediction` |
| `get_astrology_raw_data` | `raw` | `Calculate/AllPlanetData` + `AllHouseData` |
| `get_general_astro_data` | `general` | 24 `Calculate/*` endpoints |
| `get_ashtakvarga_data` | `ashtakvarga` | `Calculate/Sarvashtakavarga…` + `Bhinnashtakavarga…` |

The request URLs, parameter formats, parallel-fetch behavior, and "skip failed
endpoints" logic mirror the TypeScript implementation exactly.

## Layout

```
vedic-astrology/
├── SKILL.md                      # what the agent loads: when + how to use
├── README.md                     # this file
├── references/
│   └── interpretation.md         # how to turn raw data into a reading
└── scripts/
    └── vedastro.py               # the CLI (Python stdlib only)
```

## Quick start

```bash
# Free tier (~5 req/min). Add --api-key KEY or set VEDASTRO_API_KEY for unlimited.
python3 scripts/vedastro.py horoscope \
  --latitude 19.0760 --longitude 72.8777 \
  --time 14:30 --date 25/10/1992 --timezone +05:30 --pretty
```

Negative longitudes and timezone offsets (e.g. `--female-timezone -07:00`) are
handled automatically. See `SKILL.md` for every command and `references/` for
interpretation guidance.

> Requires outbound HTTPS access to `api.vedastro.org`. In restricted/egress-
> policy environments that host may be blocked; the CLI then exits non-zero with
> a JSON `{"error": ...}` describing the failure.
