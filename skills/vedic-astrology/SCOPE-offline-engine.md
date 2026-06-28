# Scope: a fully offline Vedic astrology engine

This document scopes replacing the VedAstro.org API dependency with a
**self-contained calculation engine** that runs locally with no network call.
Today the skill (and the original MCP server) is a thin client: it forwards
birth details to `api.vedastro.org/api/Calculate/*` and returns the JSON. To go
offline we must reproduce, ourselves, the math and rules that live behind that
API.

The goal is **functional parity with the 6 capabilities**, not a byte-for-byte
clone of VedAstro's prose.

---

## 1. The three layers, restated

| Layer | What it is | Effort to build offline |
|---|---|---|
| **Astronomical core** | Planet longitudes, ayanamsa, ascendant, houses, nodes, sunrise/set | Low–medium (a solved problem; use an ephemeris library) |
| **Vedic primitives** | Signs, lords, nakshatras, aspects, dignities, panchanga, vargas | Medium (well-documented lookup tables + rules) |
| **Interpretation** | Yoga detection, Kuta scoring, Ashtakvarga, numerology, prediction text | Medium → very high (depends how far we go) |

The decisive insight: **because an LLM consumes this skill, we do not need
VedAstro's canned prediction paragraphs.** We need to compute the *deterministic
facts* of the chart and let Claude interpret them (the skill already has
`references/interpretation.md`). That removes the single largest and most
legally fraught piece of work — the authored prediction corpus.

---

## 2. Foundation decision: which ephemeris (and license)

Every downstream number depends on planetary positions. Two viable paths:

### Option A — Swiss Ephemeris (`pyswisseph`)  ← fastest to parity
- `swe.set_sid_mode(swe.SIDM_RAMAN)` gives **Raman ayanamsa natively** — same
  system VedAstro uses, so positions match closely out of the box.
- `SEFLG_MOSEPH` (Moshier) needs **no data files** and is accurate to ~1 arcsec
  — far finer than astrology requires. Truly offline after one `pip install`.
- Built-ins for ascendant/houses (`swe.houses_ex`), nodes, rise/set
  (`swe.rise_trans`), sidereal time. Most of the astronomical core is one call
  each.
- **License: AGPL-3.0 or paid commercial.** Using it makes the engine AGPL
  unless a commercial license is purchased. This is the key trade-off.

### Option B — Skyfield (MIT) + JPL ephemeris (public domain)
- Permissive license, no copyleft.
- We compute ayanamsa, sidereal conversion, ascendant, house cusps, and
  rise/set **ourselves** (Raman ayanamsa has a published formula; houses are
  straightforward for whole-sign/equal). More code, more parity-tuning.
- A small JPL kernel (e.g. `de440s.bsp`, ~30 MB) ships with the skill, or use
  Skyfield's built-in lower-precision option.

**Recommendation:** start on **Option A** to reach parity quickly and validate
the whole pipeline against the live API; keep the ephemeris access behind a thin
interface so Option B can be swapped in later if AGPL is unacceptable. The
licensing choice is a genuine fork I need a decision on before building.

---

## 3. Capability-by-capability scope

Difficulty is for an experienced dev; "parity risk" = how hard it is to match
VedAstro's exact numbers.

### `numerology`  — **Easy**, fully offline, no ephemeris
- Chaldean letter→number map, sum, reduce to name number, ruling planet.
- Life-aspect scores + reading: compute the number; **Claude writes the
  reading** (or a small authored table). 
- Effort: ~1–2 days. Parity risk: low.

### `general` (24 properties) — **Medium**
- Needs the astronomical core + panchanga.
- Breakdown of the 24 fields:
  - Direct from core: `LagnaSignName`, `MoonSignName`, `MoonConstellation`,
    `AyanamsaDegree`, `SunriseTime`, `SunsetTime`, `DayDurationHours`,
    `IsDayBirth`, `LocalMeanTime`, `DayOfWeek`, `LordOfWeekday`.
  - Panchanga: `LunarDay` (Tithi), `NithyaYoga`, `Karana`.
  - Table lookups on Moon/Lagna: `BirthVarna`, `HoraAtBirth`, `YoniKutaAnimal`,
    `PanchaPakshiBirthBird`.
  - Rule-based: `KujaDosaScore` (Mars in houses 1/2/4/7/8/12 from references),
    `MarakaPlanetList` (2nd/7th lords + occupants), `ShubKartari`/`PaapaKartari`
    planets & houses (benefic/malefic hemming).
- Effort: ~4–6 days. Parity risk: medium (definitions vary by author; must match
  VedAstro's exact rules — verify against golden tests).

### `raw` (9 planets + 12 houses) — **Medium**
- Per planet: sidereal longitude, sign, nakshatra, house occupied, houses owned,
  sign lord, star lord, degrees, retrograde, dignity (exalt/debil/own/friend),
  combustion, Vedic aspects (7th for all; +4/8 Mars, +5/9 Jupiter, +3/10 Saturn).
- Per house: sign, lord, occupants, aspecting planets, constellation.
- Requires friendship tables, exaltation/debilitation points, aspect logic.
- Effort: ~4–6 days. Parity risk: medium (node type — mean vs true Rahu — and
  house system must match VedAstro; confirm by diffing).

### `ashtakvarga` — **Medium**, deterministic
- Bhinnashtakavarga: the 7 classical benefic-point tables (Parashari) for
  Sun…Saturn — fixed reference data, ~7×12 booleans each.
- Sarvashtakavarga: sum across planets.
- Effort: ~2–3 days. Parity risk: low (standard tables; just transcribe and
  test).

### `match` (16-Kuta) — **Medium–High**, deterministic
- Ashtakoota (Varna, Vasya, Tara/Dina, Yoni, Graha Maitri, Gana, Bhakoot/Rasi,
  Nadi) → 36-point scale, plus the extra factors VedAstro reports (Mahendra,
  Stree Deergha, Rajju, Vedha, etc.) and the percentage.
- Each factor is a table lookup keyed on the two Moon nakshatras/signs + a
  weight. Explanations: authored short strings or Claude-generated.
- Effort: ~4–6 days. Parity risk: medium (must match VedAstro's weighting and
  which 16 factors, and its percentage formula).

### `horoscope` (the predictions) — **High / open-ended**
This is where VedAstro's bulk lives: a large library of named yogas, each a
predicate over the chart producing a prediction. Three sub-tiers:
- **2a. Facts + LLM interpretation (recommended MVP):** compute placements,
  dignities, dasha (Vimshottari) and a *core* set of ~20–40 famous yogas
  (Gajakesari, Raja yogas, Dhana yogas, Pancha Mahapurusha, Kemadruma,
  Neecha Bhanga…) as booleans, then Claude writes the reading. ~5–8 days.
- **2b. Broad yoga library:** 100–200+ classical yogas encoded as predicates.
  ~2–4 weeks, ongoing.
- **2c. VedAstro-identical prose:** port their authored text corpus (AGPL) or
  author original text to hundreds of rules. Weeks–months; mostly content + IP
  work, low engineering novelty. **Recommend skipping** in favor of 2a/2b + LLM.

---

## 4. Proposed architecture

```
skills/vedic-astrology/
  engine/
    ephemeris.py      # thin interface over swe/skyfield: positions, lagna, houses, rise/set
    chart.py          # build a Chart object: planets, houses, dignities, aspects, nakshatras
    panchanga.py      # tithi, nakshatra, yoga, karana, vara, hora
    tables/           # reference data: lords, exaltations, friendships,
                      #   nakshatra→(varna,yoni,gana,nadi...), ashtakvarga tables, kuta tables
    yogas.py          # yoga predicates (tier 2a/2b)
    ashtakvarga.py
    match.py          # 16-Kuta scoring
    numerology.py
  scripts/vedastro.py # SAME CLI — add --offline flag; same 6 commands, same JSON shape
```

Keep the **exact CLI and JSON output contract** so the skill, SKILL.md, and any
caller are unchanged. `--offline` (or auto-fallback when the API is unreachable)
selects the local engine. This means the offline engine can be built and shipped
incrementally, command by command, behind the existing interface.

---

## 5. Validation strategy (non-negotiable)

The original API is the **oracle**. Build a golden-test harness:
1. Pick ~20 diverse reference charts (hemispheres, eras, day/night, edge
   timezones, leap years).
2. Capture the live API JSON for all 6 endpoints for each chart (run once from
   an environment that *can* reach `api.vedastro.org` — note: this sandbox
   cannot, egress policy blocks it).
3. Diff offline-engine output against the captured oracle; tune until:
   - positions within a small tolerance (e.g. < 1 arcminute),
   - all discrete fields (signs, nakshatras, lords, Kuta verdicts, Ashtakvarga
     bindus) match **exactly**.
4. Lock the golden files as regression tests.

Parity hinges on matching VedAstro's exact choices: **Raman ayanamsa value,
mean-vs-true nodes, house system (whole-sign vs Sripati/bhava), combustion orbs,
and Kuta weighting.** These get pinned during step 3.

---

## 6. Effort & phasing

| Phase | Deliverable | Est. (1 dev) |
|---|---|---|
| 0 | Ephemeris interface + Raman sidereal positions + golden-test harness | 3–5 days |
| 1 | `numerology` + `ashtakvarga` offline (easy wins, low risk) | 3–4 days |
| 2 | Astronomical core → `raw` + `general` offline | 1–2 weeks |
| 3 | `match` (16-Kuta) offline | 4–6 days |
| 4 | `horoscope` MVP: dasha + core yogas, LLM interprets (tier 2a) | 1–2 weeks |
| **MVP total** | **All 6 commands offline, LLM-interpreted** | **~4–5 weeks** |
| 5 (optional) | Broad yoga library (tier 2b) | +2–4 weeks |
| 6 (optional) | VedAstro-identical prose corpus (tier 2c) | +weeks–months |

Dependencies added: one ephemeris package (`pyswisseph` ~2 MB, or
`skyfield` + a JPL kernel). Still no running server, no API key, no rate limit.

---

## 7. Risks & open decisions

- **License (blocking):** AGPL (Swiss Ephemeris, fast) vs permissive (Skyfield,
  more code). Affects how this skill can be distributed. **Need a call.**
- **Parity tuning:** matching VedAstro's exact ayanamsa/node/house choices is
  empirical; budget iteration in Phase 0–3.
- **Oracle capture must happen off this sandbox** (egress blocks the API here).
- **Scope of `horoscope`:** how many yogas is "enough"? Recommend shipping
  tier 2a (facts + core yogas + LLM) and expanding the yoga library over time
  rather than chasing 1:1 prose.
- **Content/IP:** if VedAstro prose parity is required, porting their text
  inherits AGPL and attribution obligations; authoring fresh text is large.
  Recommend LLM interpretation instead.

---

## 8. Recommendation

Build the **MVP (Phases 0–4, ~4–5 weeks)** on Swiss Ephemeris behind a swappable
interface, keep the existing CLI/JSON contract with an `--offline` switch, and
let Claude handle interpretation rather than cloning VedAstro's prose. That
yields all six capabilities running fully offline, validated against the live
API as oracle, with the heavy/legally-sensitive content work deliberately out of
scope.

Two decisions unblock the build: **(1)** ephemeris/license path, and **(2)** how
far up the `horoscope` yoga tiers to go for v1.
