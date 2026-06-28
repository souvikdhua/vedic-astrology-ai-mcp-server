# Interpreting VedAstro output

The CLI returns structured JSON. Your job is to translate it into a clear,
human reading. This reference explains the shape of each command's output and
how to present it responsibly.

## General principles

- **Lead with the strongest, clearest signals.** Don't dump every field —
  synthesize. Group findings by life area (personality, career, wealth,
  relationships/marriage, health, spirituality).
- **Name the technical basis briefly** ("Jupiter aspecting the 10th house
  suggests…") so the reading feels grounded, but keep the language accessible.
- **Frame appropriately.** This is traditional Vedic astrology offered for
  reflection and cultural interest — not deterministic prophecy, and not
  medical, legal, psychological, or financial advice. Avoid fatalistic or
  alarming phrasing, especially around health, death/longevity, and marriage.
- **All charts use the Raman Ayanamsa.** Mention it if the user compares against
  another source (Lahiri is the common alternative and will differ slightly).

## `horoscope`

Returns a large set of named prediction objects, each typically with a name,
description, and the planets/houses that triggered it. These already read as
sentences. Cluster them by theme rather than listing all of them, and surface
the most significant yogas (e.g. Raja yogas, Dhana yogas) prominently.

## `match`

Returns an overall **Kuta score percentage** plus the 16 Kuta factors (Dina,
Gana, Mahendra, Stree Deergha, Rasi, Graha Maitri, Vasya, Rajju, Vedha, Varna,
Yoni, Nadi, etc.). Each factor carries a Good/Bad rating and an explanation.

- Lead with the overall percentage and a one-line verdict.
- Highlight the heavily weighted factors (Nadi, Rasi/Bhakoot, Gana) and any
  that are flagged Bad, with their explanations.
- Be balanced and non-alarming; a moderate score is not a verdict on a
  relationship's real-world success.

## `numerology`

Returns the name number, its ruling planet, a prediction, and life-aspect scores
(Finance, Romance, Education, Health, Family, Growth, Career, Reputation,
Spirituality, Luck). Summarize the ruling planet's character, then the top and
bottom life aspects.

## `raw`

Returns `PlanetData` (9 planets) and `HouseData` (12 houses) with sign
placement, constellation/nakshatra, house occupied, houses owned, sign/star
lords, exact degrees, retrograde status, and aspects. This is the underlying
chart. Use it to answer specific questions ("where is my Moon?", "is Mars
retrograde?") or to build a custom analysis. Translate house numbers into their
significations (1st = self/body, 7th = marriage/partnership, 10th = career, etc.).

## `general`

Returns ~24 single-value properties. Useful quick facts:

- **LagnaSignName** — Ascendant/rising sign.
- **MoonSignName / MoonConstellation** — Rashi and Nakshatra (key in Vedic work).
- **LunarDay (Tithi), NithyaYoga, Karana** — Panchanga elements.
- **SunriseTime / SunsetTime / IsDayBirth / DayDurationHours** — birth context.
- **KujaDosaScore** — Mangal/Kuja Dosha strength (relevant to match analysis).
- **MarakaPlanetList** — maraka (life-event) planets.
- **ShubKartari / PaapaKartari Planets & Houses** — benefic/malefic enclosure.
- **BirthVarna, HoraAtBirth, DayOfWeek, LordOfWeekday, PanchaPakshiBirthBird** —
  classification details.

Some endpoints occasionally fail and are silently omitted from the result; only
report the keys that are present.

## `ashtakvarga`

Returns `SarvashtakavargaChart` (combined bindu strength of all planets across
the 12 signs, with totals) and `BhinnashtakavargaChart` (each planet's individual
contribution). Higher bindu counts in a sign indicate greater strength/benefit
there — useful for transit timing. Point the user to their strongest and weakest
signs and explain what transits through those areas may emphasize.
