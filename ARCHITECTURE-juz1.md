# Tafsir — Juz 1 Expansion Architecture

## Scope

Expand the study framework from Al-Fatihah (7 ayahs) to the full **Juz 1** (148 ayahs: Al-Fatihah 1:1–7 + Al-Baqarah 2:1–141). The user must be able to navigate by **Juz, Surah, Ayah, or Page**.

## Navigation Model

Four navigation dimensions, one canonical index. The index is the single source of truth for all routing.

```
DIMENSION          LOOKUP                        RESOLVES TO
─────────          ──────                         ────────────
Juz (1-30)         navigation-<juz>.json          ayah range [start, end]
Surah (1-114)      navigation-<juz>.json          surah list with ayah ranges
Ayah (verse_key)   navigation-<juz>.json          page, juz, surah
Page (1-604)       navigation-<juz>.json          ayah range on that page
```

All four dimensions resolve to **verse_key** (`surah:ayah`) — the atomic unit the data layer joins on.

## Juz 1 Facts (from API, verified)

| Metric | Value |
|--------|-------|
| Total ayahs | 148 |
| Surahs | 1 (Al-Fatihah, 7 ayahs), 2 (Al-Baqarah, 1–141) |
| Pages | 1–21 (Madani mushaf page numbering) |
| Global ayah range | 1–148 |

## Data Organization

**One data file per surah** — not one giant juz file. Modular, loadable, maintainable.

```
gc1/
├── navigation-juz1.json      ← navigation index (built ✓)
├── data/
│   ├── surah-1.json          ← Al-Fatihah (7 ayahs, exists as seed-fatihah.json)
│   ├── surah-2.json          ← Al-Baqarah 1-141 (to be built)
│   ├── themes.json           ← placeholders (exist)
│   ├── cross-references.json ← placeholders (exist)
│   ├── per-page-analysis.json← awaiting user content
│   └── practical-application.json ← awaiting user content
```

**Data file schema** (uniform with existing seed-fatihah.json):

```json
{
  "meta": {
    "surah": 2,
    "surah_name": "Al-Baqarah",
    "surah_name_arabic": "البقرة",
    "total_ayahs": 141,
    "juz_range": [1, 1],
    "page_range": [2, 21],
    "source_ids": { ... },
    "verification_status": { "grammar_system": "verified", "tafsir_content": "sourced" },
    "complexity_levels": { ... }
  },
  "ayahs": [
    {
      "ayah_number": 1,
      "verse_key": "2:1",
      "arabic": "...",
      "page": 2,
      "juz": 1,
      "words": [ ... per-word morphology, wazn, occurrences ... ],
      "tafsir": [ ... per-edition, sourced ... ]
    }
  ]
}
```

## Content Availability by Layer (Juz 1)

| Layer | Al-Fatihah | Al-Baqarah 1-141 | Source |
|-------|-----------|------------------|--------|
| Verse text + words | ✓ built | Need ETL | Quran Fdn API / Corpus |
| Word-by-word translation | ✓ built | Need ETL | Corpus |
| Morphology | ✓ built | Need ETL | Corpus |
| Wazn (verified) | ✓ 29 words annotated | Need annotation (141 ayahs ~ many words) | Manual (MVP standard) |
| Occurrences | ✓ built | Need ETL | Corpus |
| Tafsir (Jalalayn + Ibn Kathir) | ✓ built | Need ETL | spa5k API |
| Asbab al-Nuzul | absent (sparse layer) | ~9-13% coverage | spa5k ed. 86 |
| Cross-refs / themes | placeholder | placeholder | roadmap |
| Per-page analysis | awaiting user content | awaiting user content | user |
| Practical application | awaiting user content | awaiting user content | user |

## Scaling Strategy (the key architectural decision)

**Wazn annotation is the bottleneck.** 29 words (Al-Fatihah) took manual annotation. Al-Baqarah 1-141 has ~2,700 words. Manual annotation of the whole juz at the same per-word quality is a large task.

**Recommended:** Al-Baqarah 1-141 gets full verse/word/translation/morphology/tafsir data via ETL (mechanical, KodeKoot's pipeline), but **wazn annotation proceeds progressively** — a verified subset first (e.g., the first few ayahs or high-frequency roots), expanded over time. The framework already handles absence gracefully: words without wazn simply don't show the Pattern section (same as proper nouns/pronouns today).

This preserves the "accuracy over coverage" principle — we never show an unverified pattern. Coverage grows as verification completes.

## Navigation UI Requirements

The four-dimension navigation needs a control surface in the study pane:

1. **Juz selector** — 30 parts (only 1 active now; others disabled/grayed until data exists)
2. **Surah selector** — within active juz (1: Al-Fatihah, 2: Al-Baqarah)
3. **Ayah navigation** — prev/next + jump-to-ayah within surah
4. **Page navigation** — prev/next page (page 1-21 for juz 1) or jump-by-page

All four resolve to a verse_key; the study surface renders from that key. The same rendering code path serves all four entry points.

## Build Order

1. **ETL for Al-Baqarah 1-141** — verse, words, translation, morphology, tafsir → `data/surah-2.json` (KodeKoot)
2. **Navigation UI** — juz/surah/ayah/page controls resolving to verse_key (KodeKoot + Shayba)
3. **Data loader** — study pane loads `data/surah-N.json` on demand (juz 1 = surah 1 + 2) (KodeKoot)
4. **Wazn progressive annotation** — verified subset of Al-Baqarah, expanded over time (Sheikh Al-Jabr)
5. **Content integration** — per-page analysis + practical application when user provides (all)

## Interfaces

- **Data layer → Study surface**: verse_key is the join key. No other contract needed.
- **Navigation index → Data layer**: navigation-juz1.json says "juz 1 = surahs [1,2], pages [1,21]" → loader fetches surah-1.json + surah-2.json.
- **Study surface → User**: one rendering path for verse_key, four navigation entry points.

## Verification

- Juz 1 navigation index: 148 ayahs, surahs [1,2], pages [1,21] (verified against API ✓)
- Data files load without error in study pane
- Navigate by juz → sees Fatihah; by surah → sees either surah; by ayah → jumps to 2:141; by page → page 21 shows last ayahs of juz 1
- Word tap still opens study pane with root/morphology/wazn/tafsir/occurrences
