# Wazn Pipeline — Known Issues & Audit Notes

> Living log for the progressive wazn annotation (Al-Baqarah 1–141, Juz 1).
> Every entry stays **pending** until hand-verified in the audit loop; nothing here is
> promoted without QA confirmation. Shape-layer output is surface-true but function-blind.

## Shape layer (auto-derivation) blind spots

| # | Location | Word | Wrong auto-output | Correct | Status |
|---|----------|------|-------------------|---------|--------|
| 1 | 2:23:14, 2:133:3 | شُهَدَاء | فَعِيل (lemma شَهِيد is فَعِيل, surface is plural) | فُعَلَاء (broken plural of شَهِيد) | FIXED — concordance guard rejects; now null/pending; curate manually |
| 2 | 2:85:17 | أُسَارَى | فَعِيل (lemma أَسِير is فَعِيل, surface is plural) | فُعَالَى (broken plural of أَسِير) | FIXED — concordance guard rejects; now null/pending; curate manually |

**Rule codified 2026-08-28:** shape claims fire ONLY when the de-cliticized surface
core equals the plain lemma. Broken plurals and other surface≠lemma forms are rejected
automatically and stay in the manual pool. 4-letter family only — anything longer is
plural/derived territory.

## Verb form vowel defaults (auto layer, Form I imperfect)

| Location | Word | Auto default | Corpus lemma | Correct wazn |
|----------|------|--------------|--------------|--------------|
| 2:15:4 | يَمُدُّهُمْ | يَفْعَلُ (default) | مَدَّ (geminate) | يَفْعُلُ |
| 2:18:6 | يَرْجِعُونَ | يَفْعَلُ (default) | رَجَعَ (kasra) | يَفْعِلُ |

**Rule:** Form I imperfect vowels are not determinable from root alone — defaults are
pending-only, corrected during audit. IMPF1_VOWELS overrides known verbs.

## Verbal nouns (مصدر)

VN patterns depend on root class (weak/geminate/hamzated). Auto layer emits **null +
explanatory note** — never a guessed pattern. Manual curation required. Count: 16 in
2:1–2:20 (طُغْيَان, حَذَر, قَوْل, إِحْسَان, إِيمَان, إِخْرَاج, …).

## Particles / pronouns / proper nouns

Null wazn by design. Allah (الله) is a proper noun with no derivational pattern — every
occurrence marked so. Compound particles (كُلَّمَا) and locatives (عَلَى, فَوْقَ) carry
explanatory notes, no pattern.

## Verification status semantics

- `verified` — human-curated against classical sarf AND corpus feature tags (QA-gated)
- `pending` — auto-derived or surface-derived; **never shown as fact to users**
- Pattern may be surface-true while function (participle vs adjective) is unconfirmed —
  flagged with `wazn_note: pattern surface-derived, function pending`

## Batch ledger

| Batch | Range | Verified count | QA verdict |
|-------|-------|----------------|------------|
| 1 | 2:1–2:10 | 92 | PASS (Halakukhan) |
| 2 | 2:11–2:20 | 138 (→230 total) | PASS (Halakukhan) |