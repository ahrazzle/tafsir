# Tafsir — ETL Design: spa5k Tafsir Wiring

**Stage handoff (Team6 stage 4 → 8):** Sheikh → Azaraki (analysis/ETL design) → KodeKoot (pipeline). This document is the build spec for @kodekoot.

## Goal

Populate `ayah.tafsir[]` across Juz 1 (surah 1 + surah 2:1–141) with live, verified tafsir text from the spa5k/tafsir_api endpoint. No fabricated text. Accuracy-over-coverage gate preserved.

## Source Endpoint (verified live 2026-08-28)

```
GET https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/{spa5k_slug}/{surah}.json
→ { "ayahs": [ { "ayah": <int>, "surah": <int>, "text": <string> }, ... ] }
```

- **Verified:** `en-al-jalalayn/2.json` → HTTP 200, 4,580 bytes
- **Verified:** `en-tafisr-ibn-kathir/1.json` → HTTP 200, 203,604 bytes, real Ibn Kathir text
- **Shape:** dict with `ayahs` array; full surah returned (contiguous 1..N, no gaps)
- **License:** spa5k repo = MIT; classical texts public domain; published editions (Ma'arif, Muyassar, Tazkirul, Zilal) carry `license: "published"` — attribute, don't modify.

## Registry → Endpoint Map

13 editions from `data/tafsir-registry.json`. ETL iterates the `default_order` array; each edition maps `source_id` → `spa5k_slug`.

| source_id | spa5k_slug | lang | license |
|-----------|-----------|------|---------|
| spa5k-en-al-jalalayn | en-al-jalalayn | en | public_domain |
| spa5k-en-tafisr-ibn-kathir | en-tafisr-ibn-kathir | en | public_domain |
| spa5k-en-maarif | en-tafsir-maarif-ul-quran | en | published |
| spa5k-ar-muyassar | ar-tafsir-muyassar | ar | published |
| spa5k-ar-saddi | ar-tafseer-al-saddi | ar | public_domain |
| spa5k-ar-tabari | ar-tafsir-al-tabari | ar | public_domain |
| spa5k-ar-qurtubi | ar-tafseer-al-qurtubi | ar | public_domain |
| spa5k-ar-baghawi | ar-tafsir-al-baghawi | ar | public_domain |
| spa5k-en-tazkirul | en-tazkirul-quran | en | published |
| spa5k-en-zilal | tafsir-fe-zalul-quran-syed-qatab | en | published |
| spa5k-ar-baydawi | tafsir-al-baydawi | ar | public_domain |
| spa5k-ar-tahrir | ar-tafsir-al-tahrir-al-tanwir | ar | public_domain |
| spa5k-ar-alusi | tafsir-al-alusi | ar | public_domain |

## Merge Contract — `ayah.tafsir[]` entry

Each tafsir entry in `ayah.tafsir[]` matches the schema already used in `surah-1.json`:

```json
{
  "source_id": "spa5k-en-al-jalalayn",
  "source_name": "Tafsir al-Jalalayn",
  "author": "Jalal ad-Din al-Mahalli & Jalal ad-Din as-Suyuti",
  "text": "<full verse commentary, verbatim from endpoint>",
  "verification_status": "sourced",
  "complexity_level": 2,
  "license": "public_domain"
}
```

## ETL Pipeline Steps

### Step 1 — Fetch (per edition × per surah)
For each edition in `default_order`, for each surah in [1, 2]:
```
GET /tafsir/{slug}/{surah}.json
```
Juz 1 needs surah 1 (7 ayahs) + surah 2 (filtered to 1–141). The endpoint returns full surah; **filter to Juz 1 range** (2:1–141) at write time — don't store ayahs beyond the juz.

### Step 2 — Map to ayah key
Build lookup `verse_key → text` from each edition's `ayahs` array:
```
verse_key = f"{entry['surah']}:{entry['ayah']}"
```

### Step 3 — Merge into `ayah.tafsir[]`
For each ayah in the target data file (surah-1.json, surah-2.json):
- Clear existing `tafsir: []`
- For each edition (in `default_order` order), look up `verse_key` in the edition's map
- If present → append the tafsir entry object
- If absent → skip (do not fabricate; do not leave a placeholder)

**Result:** every ayah in Juz 1 gets up to 13 tafsir entries; ayahs with no text in a given edition simply don't include that edition.

### Step 4 — Preserve existing embedded tafsir
`surah-1.json` already has Jalalayn + Ibn Kathir embedded. The ETL re-fetches these from the same endpoint — the fetched text should match. If a diff appears, the fetched version wins (it's the canonical spa5k source), but log any discrepancy for QA.

### Step 5 — QA gate (Halakukhan)
- **No fabricated text:** every `text` must trace to a fetched endpoint payload. Spot-check 3 ayahs per edition against the raw endpoint.
- **Completeness:** surah-1 → 7 ayahs; surah-2 → 141 ayahs (juz 1 range).
- **Contiguity:** no edition should have gaps where the endpoint had data.
- **Attribution:** `source_id`, `source_name`, `author`, `license` correct per registry.
- Log: editions × surahs fetched, ayahs populated per edition, any misses.

## Output Files

```
data/surah-1.json   ← tafsir[] populated (7 ayahs × ≤13 editions)
data/surah-2.json   ← tafsir[] populated (141 ayahs × ≤13 editions)
```

## Interfaces / Dependencies

- **Reads:** `data/tafsir-registry.json` (editions + slugs + metadata)
- **Writes:** `data/surah-1.json`, `data/surah-2.json`
- **Does NOT touch:** `navigation-juz1.json`, word/morphology/wazn data, `index.html` rendering logic
- **Rendering:** index.html already reads `ayah.tafsir[]` — once populated, the single-source tafsir switcher works across Juz 1 with all 13 editions. No UI change needed.

## Design Decisions

1. **ETL is a build-time script, not runtime fetch.** The tafsir text is baked into the JSON files. This keeps the app `file://`-friendly for the standalone study pane and avoids runtime API dependency/rate limits. (Runtime streaming of all editions is a v2+ concern.)
2. **Filter to Juz 1 at write time.** We only persist 2:1–141, not all 286 of Baqarah, keeping data files scoped to the current expansion.
3. **13 editions all wired, but UI scopes.** The registry's default_order includes contemporary editions (Zilal, Tazkirul). The source chooser (v2) will let users pick; for now all 13 populate but the UI's default switcher shows the classical set first (per registry default_order). No edition is excluded from data.
4. **Arabic editions render as-is.** The study pane already handles Arabic; language is a per-source attribute surfaced in the source metadata.

## Acceptance Criteria

- [ ] `data/surah-2.json` `tafsir[]` populated for all 141 ayahs
- [ ] `data/surah-1.json` `tafsir[]` matches current embedded Jalalayn + Ibn Kathir (or logs clean diff)
- [ ] Every tafsir text traces to a fetched spa5k payload (QA spot-check)
- [ ] Single-source switcher in index.html shows all 13 editions on a Juz 1 ayah
- [ ] No fabricated/placeholder tafsir text anywhere
