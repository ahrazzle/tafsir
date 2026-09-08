# Tafsir — Quran-Wide Scaffolding Architecture (30 Juz / 114 Surah / 604 Pages)

> Evolved from `ARCHITECTURE-juz1.md`. The Juz 1 doc remains the canonical
> reference for the *content/ETL* decision (wazn bottleneck, progressive annotation).
> This document governs the *data + routing layer* that now spans the entire Quran,
> and the convention every subsequent juz must follow.

## 1. The invariant the whole system resolves on

**`verse_key` (`surah:ayah`) is the atomic join key.** Every navigation dimension
— juz, surah, ayah, page — resolves to a `verse_key`. The data layer joins on it.
This is unchanged from Juz 1.

## 2. Four navigation dimensions, one canonical index

| Dimension   | Lookup file                        | Resolves to                         |
|-------------|------------------------------------|-------------------------------------|
| Juz (1–30)  | `navigation.json` → `juz`          | surah list + page span              |
| Surah (1–114)| `navigation.json` → `surahs`       | file + pages + juz membership       |
| Page (1–604)| `navigation.json` → `pages`        | surah + ayah range + juz            |
| Ayah        | any `data/surah-N.json`            | `verse_key`                         |

`navigation.json` is the **consolidated** index the UI loads. It mirrors the 30
per-juz files (`navigation-juzN.json`) exactly. Either can be the source of truth;
the consolidated file is generated FROM the per-juz files, so the per-juz files are
the authoritative artifacts and `navigation.json` is the derived join table.

### Per-juz file (`navigation-juzN.json`) schema
```
meta      : { description, juz, total_ayahs, source, fetched }
juz       : { number, surah_range:{start,end}, ayah_range:{start,end} }
surahs     : [ { surah, name, english_name, translation, revelation_type,
                ayah_start, ayah_end, page_start, page_end } ]
pages      : { "<page>": { page, surah, ayah_start, ayah_end } }
ayah_index : [ { global_number, surah, ayah_in_surah, verse_key, page, juz } ]
```
Source for juz 2–30: `api.alquran.cloud/v1/juz/N` (same API as Juz 1). Juz 1 file is
the original curated artifact and was NOT regenerated.

## 3. Data organization — one file per surah

```
gc1/
├── navigation.json            ← consolidated routing index (UI loads this)
├── navigation-juzN.json       ← per-juz authoritative routing (N = 1..30)
├── ARCHITECTURE.md            ← this file
├── ARCHITECTURE-juz1.md       ← Juz 1 ETL/annotation decision (still canonical)
├── KNOWN-ISSUES.md            ← audit log (scaffolding + wazn)
├── index.html                 ← study surface (now Quran-wide)
├── study-pane.html            ← standalone pane (Fatihah seed, unchanged)
├── data/
│   ├── surah-1.json           ← Al-Fatihah  (REAL, fully populated)
│   ├── surah-2.json           ← Al-Baqarah  (REAL, ETL'd; wazn progressive)
│   ├── surah-3.json … surah-114.json  ← SCAFFOLDS (meta-complete, ayahs:[])
│   ├── themes.json / cross-references.json / per-page-analysis.json / practical-application.json
└── (tooling) wazn-derive.py, arabic_normalize.py, curated_batch_2.py, …
```

**Rule:** `data/surah-N.json` exists for **every** surah 1–114. Surahs 1–2 carry
real content. Surahs 3–114 are **scaffolds**: `meta` is fully populated (name,
arabic name, revelation type, juz membership, page range, per-juz ayah counts,
`content_status:"scaffold"`, `verification_status` all `pending_etl`), and
`ayahs:[]` is empty by design — no verses are synthesized. The UI shows a "Scaffold"
notice for these, so routing is 100% live while content fills in per juz.

## 4. Scaffold meta shape (mirrors production `surah-2.json`)

```json
{
  "meta": {
    "surah": 112,
    "surah_name": "Al-Ikhlaas",
    "surah_name_arabic": "الإخلاص",
    "revelation_type": "Meccan",
    "juz": [30],
    "total_ayahs": 4,
    "page_range": [598, 598],
    "ayahs_per_juz": {"30": 4},
    "verification_status": {
      "verse_text": "pending_etl",
      "morphology": "pending_etl",
      "wazn": "pending_etl"
    },
    "content_status": "scaffold",
    "note": "Meta-complete scaffold. Verse/word/… content to be populated by the ETL pipeline (KodeKoot) per the progressive-annotation convention in ARCHITECTURE-juz1.md. No verses synthesized."
  },
  "ayahs": []
}
```

## 5. Content availability by layer (whole Quran)

| Layer | Juz 1 (1–2) | Juz 2–30 (3–114) | Source |
|-------|-------------|------------------|--------|
| Verse text + words | ✓ built | Scaffold (ETL pending) | Quran Fdn API / Corpus |
| Word-by-word translation | ✓ built | ETL pending | Corpus |
| Morphology | ✓ built | ETL pending | Corpus |
| Wazn (verified) | 2:1–2:20 verified; rest pending | ETL pending → progressive | Manual / wazn-derive.py |
| Occurrences | ✓ built | ETL pending | Corpus |
| Tafsir (Jalalayn + Ibn Kathir) | ✓ built | ETL pending | spa5k API |
| Asbab al-Nuzul | sparse layer | sparse layer | spa5k ed. 86 |
| Cross-refs / themes | placeholder | placeholder | roadmap |
| Per-page analysis | awaiting user | awaiting user | user |
| Practical application | awaiting user | awaiting user | user |

## 6. Scaling strategy (unchanged principle)

**Accuracy over coverage.** We never show an unverified verse, pattern, or tafsir
line. Wazn is the bottleneck (see `ARCHITECTURE-juz1.md` §Scaling Strategy and
`KNOWN-ISSUES.md` §Wazn). Each juz's content is filled by the same ETL pipeline that
produced `surah-2.json`, with wazn annotated progressively and gated by QA before any
`verified` flag is set.

## 7. Front-end contract

- `index.html` loads `navigation.json` (HTTP only — `file://` is blocked by the
  browser; it shows a help banner with the `python3 -m http.server` command).
- The `juzSelect` drives which surahs appear in `surahSelect`; `surahSelect` +
  `pageSelect` resolve to a `verse_key`; the study surface renders from that key.
- `NAV.surahs[N].content` is the flag: `true` → render verses; `false` → render the
  scaffold notice. **This is the only branch that decides real-vs-pending content.**
- Verified global totals (generated 2026-08-28, cross-checked three ways): 114
  surahs, 30 juz, 604 pages, 6236 ayahs.

## 8. Build order for the remaining 28 juz

1. ETL each surah's verse/word/translation/morphology/tafsir → `data/surah-N.json`
   (KodeKoot's pipeline, mirroring `surah-2.json`).
2. Set `meta.content_status: "populated"` and `verification_status` per layer as ETL
   completes; flip `NAV.surahs[N].content` to `true` in `navigation.json`.
3. Progressive wazn annotation per the `ARCHITECTURE-juz1.md` convention
   (Sheikh Al-Jabr, QA-gated via `KNOWN-ISSUES.md`).
4. Content integration (per-page analysis, practical application) when user provides.

## 9. Regeneration / provenance

- `navigation-juzN.json` (N=2..30) and `navigation.json`: generated 2026-08-28 from
  `api.alquran.cloud/v1/juz/N` + `_surah_master.json` (114-surah master from
  `api.alquran.cloud/v1/surah`). Deterministic; no LLM involved. Totals reconciled to
  6236 ayahs three independent ways.
- `data/surah-3..114.json`: scaffolds generated 2026-08-28 from the same master.
- `_surah_master.json` / `_surah_master_raw.json`: scratch provenance, safe to delete;
  not part of the runtime contract.

## 10. Verification (this build)

- 154 JSON files parse clean.
- Global ayah total = 6236 (sum of surah counts = sum of juz totals = sum of
  `ayah_index` lengths in per-juz files).
- All 114 `data/surah-N.json` present; 3–114 carry `content_status:"scaffold"` and
  empty `ayahs`.
- `index.html` inline JS passes `node --check`; rendered end-to-end in a DOM harness
  (juz select = 30, Surah 1 = 7 cards/29 words, Surah 114 = scaffold notice, Juz 30
  navigation, page-2 filter on Surah 2 = 5 ayahs). Two init bugs caught and fixed
  during the harness run (missing `juzSelect` declaration; premature `populateJuzSelect`
  before `NAV` loaded).
