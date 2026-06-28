#!/usr/bin/env python3
"""
VedAstro CLI — Vedic astrology calculations powered by the VedAstro.org API.

This is the "sublimated" form of the VedAstro MCP server: the same six
capabilities, packaged as a dependency-free command-line tool that an agent
can call directly instead of connecting to a hosted MCP endpoint.

All calculations use the Raman Ayanamsa system (Swiss Ephemeris engine).
Only the Python standard library is required (urllib + json + argparse).

Birth-parameter conventions (identical to the original MCP server):
  - date     : DD/MM/YYYY        e.g. 25/10/1992
  - time     : HH:MM (24-hour)   e.g. 14:30
  - timezone : +HH:MM / -HH:MM   e.g. +05:30
  - latitude / longitude : decimal degrees, e.g. 19.0760 / 72.8777

An optional API key (free tier = 5 req/min, $1/mo = unlimited) may be passed
via --api-key or the VEDASTRO_API_KEY environment variable.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

VEDASTRO_API = "https://api.vedastro.org/api"
AYANAMSA = "RAMAN"


def _fetch(url, api_key=None):
    """GET a VedAstro endpoint and return the unwrapped Payload.

    Raises RuntimeError on HTTP failures or a non-"Pass" API status.
    """
    headers = {"x-api-key": api_key} if api_key else {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"VedAstro API HTTP error {e.code} for {url}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error reaching VedAstro: {e.reason}") from e

    data = json.loads(body)
    if data.get("Status") != "Pass":
        raise RuntimeError(f"VedAstro API error: {data.get('Payload')}")
    return data["Payload"]


def _time_location(args):
    """Build the shared /Location/.../Time/.../Ayanamsa/RAMAN URL segment."""
    return (
        f"/Location/{args.latitude},{args.longitude}"
        f"/Time/{args.time}/{args.date}/{args.timezone}"
        f"/Ayanamsa/{AYANAMSA}"
    )


# ── Command implementations ──────────────────────────────────────────────

def cmd_horoscope(args):
    url = f"{VEDASTRO_API}/Calculate/HoroscopePredictions{_time_location(args)}"
    return _fetch(url, args.api_key)


def cmd_match(args):
    url = (
        f"{VEDASTRO_API}/Calculate/MatchReport"
        f"/Location/{args.male_latitude},{args.male_longitude}"
        f"/Time/{args.male_time}/{args.male_date}/{args.male_timezone}"
        f"/Location/{args.female_latitude},{args.female_longitude}"
        f"/Time/{args.female_time}/{args.female_date}/{args.female_timezone}"
        f"/Ayanamsa/{AYANAMSA}"
    )
    return _fetch(url, args.api_key)


def cmd_numerology(args):
    name = urllib.parse.quote(args.name, safe="")
    url = f"{VEDASTRO_API}/Calculate/NameNumberPrediction/FullName/{name}"
    return _fetch(url, args.api_key)


def cmd_raw(args):
    seg = _time_location(args)
    with ThreadPoolExecutor(max_workers=2) as ex:
        planet = ex.submit(
            _fetch, f"{VEDASTRO_API}/Calculate/AllPlanetData/PlanetName/All{seg}", args.api_key
        )
        house = ex.submit(
            _fetch, f"{VEDASTRO_API}/Calculate/AllHouseData/HouseName/All{seg}", args.api_key
        )
        return {"PlanetData": planet.result(), "HouseData": house.result()}


GENERAL_ENDPOINTS = [
    "LocalMeanTime", "AyanamsaDegree", "YoniKutaAnimal", "MarakaPlanetList",
    "LagnaSignName", "MoonSignName", "MoonConstellation", "SunriseTime",
    "SunsetTime", "NithyaYoga", "Karana", "DayDurationHours", "IsDayBirth",
    "LunarDay", "BirthVarna", "HoraAtBirth", "DayOfWeek", "LordOfWeekday",
    "ShubKartariPlanets", "PaapaKartariPlanets", "ShubKartariHouses",
    "PaapaKartariHouses", "KujaDosaScore", "PanchaPakshiBirthBird",
]


def cmd_general(args):
    seg = _time_location(args)

    def one(endpoint):
        try:
            payload = _fetch(f"{VEDASTRO_API}/Calculate/{endpoint}{seg}", args.api_key)
            # Payload is a dict keyed by the endpoint name; unwrap it.
            value = payload.get(endpoint) if isinstance(payload, dict) else payload
            return endpoint, value
        except Exception:
            return endpoint, None  # skip failed endpoints, like the MCP server

    combined = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for key, value in ex.map(one, GENERAL_ENDPOINTS):
            if value is not None:
                combined[key] = value
    return combined


def cmd_ashtakvarga(args):
    seg = _time_location(args)
    with ThreadPoolExecutor(max_workers=2) as ex:
        sarva = ex.submit(
            _fetch, f"{VEDASTRO_API}/Calculate/SarvashtakavargaChart{seg}", args.api_key
        )
        bhinna = ex.submit(
            _fetch, f"{VEDASTRO_API}/Calculate/BhinnashtakavargaChart{seg}", args.api_key
        )
        return {
            "SarvashtakavargaChart": sarva.result(),
            "BhinnashtakavargaChart": bhinna.result(),
        }


# ── Argument parsing ─────────────────────────────────────────────────────

def _add_birth_args(p, prefix="", required=True):
    """Attach the standard 5 birth parameters to a subparser."""
    pre = f"--{prefix}" if prefix else "--"
    dest_prefix = prefix.replace("-", "_") if prefix else ""

    def name(field):
        return f"{pre}{field}" if prefix else f"--{field}"

    p.add_argument(name("latitude"), dest=f"{dest_prefix}latitude" if prefix else "latitude",
                   required=required, help="Latitude in decimal degrees (e.g. 19.0760)")
    p.add_argument(name("longitude"), dest=f"{dest_prefix}longitude" if prefix else "longitude",
                   required=required, help="Longitude in decimal degrees (e.g. 72.8777)")
    p.add_argument(name("time"), dest=f"{dest_prefix}time" if prefix else "time",
                   required=required, help="Birth time HH:MM 24h (e.g. 14:30)")
    p.add_argument(name("date"), dest=f"{dest_prefix}date" if prefix else "date",
                   required=required, help="Birth date DD/MM/YYYY (e.g. 25/10/1992)")
    p.add_argument(name("timezone"), dest=f"{dest_prefix}timezone" if prefix else "timezone",
                   required=required, help="Timezone offset +HH:MM/-HH:MM (e.g. +05:30)")


def build_parser():
    # Common flags, accepted both before AND after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--api-key",
        default=os.environ.get("VEDASTRO_API_KEY"),
        help="VedAstro API key for unlimited requests (or set VEDASTRO_API_KEY).",
    )
    common.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output."
    )

    parser = argparse.ArgumentParser(
        prog="vedastro",
        parents=[common],
        description="Vedic astrology calculations via the VedAstro.org API (Raman Ayanamsa).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("horoscope", parents=[common],
                       help="Full horoscope life predictions for one person.")
    _add_birth_args(p)
    p.set_defaults(func=cmd_horoscope)

    p = sub.add_parser("match", parents=[common],
                       help="Compatibility / Kuta match report between two people.")
    _add_birth_args(p, prefix="male-")
    _add_birth_args(p, prefix="female-")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("numerology", parents=[common],
                       help="Chaldean name-number prediction.")
    p.add_argument("--name", required=True, help="Name (person, business, project, number...).")
    p.set_defaults(func=cmd_numerology)

    p = sub.add_parser("raw", parents=[common],
                       help="Raw data for all 9 planets and 12 houses.")
    _add_birth_args(p)
    p.set_defaults(func=cmd_raw)

    p = sub.add_parser("general", parents=[common],
                       help="24 general chart properties (Lagna, Moon sign, Tithi...).")
    _add_birth_args(p)
    p.set_defaults(func=cmd_general)

    p = sub.add_parser("ashtakvarga", parents=[common],
                       help="Sarvashtakavarga + Bhinnashtakavarga charts.")
    _add_birth_args(p)
    p.set_defaults(func=cmd_ashtakvarga)

    return parser


def _merge_negative_values(argv):
    """Rewrite `--flag -07:00` -> `--flag=-07:00`.

    argparse treats a value beginning with '-' as another option, which breaks
    negative timezone offsets (e.g. -07:00) and negative longitudes. Any token
    that looks like a negative number/offset (`-` followed by a digit) is glued
    onto the preceding value-taking long flag.
    """
    out, i = [], 0
    while i < len(argv):
        tok = argv[i]
        if (
            tok.startswith("--")
            and tok != "--pretty"
            and "=" not in tok
            and i + 1 < len(argv)
        ):
            nxt = argv[i + 1]
            if len(nxt) > 1 and nxt[0] == "-" and nxt[1].isdigit():
                out.append(f"{tok}={nxt}")
                i += 2
                continue
        out.append(tok)
        i += 1
    return out


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    argv = _merge_negative_values(argv)
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
