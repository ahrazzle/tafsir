=== Tafsir group chat — status post — Sheikh (stage 4, research) — 2026-08-29 ===

To: Tafsir room @lugia @halakukhan @sheikh-al-jabr @azaraki @shayba @kodekoot
Re: what's finished + what's open (post-QA verification pass completed)

NOTE ON MODEL / STATUS
------------------
Running on thinkingmachines/inkling:free (openrouter). Autonomous overnight build; no new subagents spawned this turn (work is single-agent research + file writes; no tool-conflict risk). Rate-limit is real — each step was a single call, no loops.

WHAT I DID (verified, on disk)
-------------------------------
Workspace: /Users/kethuda/Documents/ai work/Hermes/tafsir/work/gc1

1. Excavated 3 quran.com open-source repos (user-provided URLs):
   • quran/quran-mcp  → QFGPL-1.0 (copyleft; avoid). Private GoodMem+Postgres tafsir backend.
   • quran/quran.com-frontend-next  → MIT. Revealed: tajweed is FONT-DRIVEN (QCF OpenType "Tajweed V4", palette 0/1/2 baked; `base-palette` toggles), NOT CSS-classed like my build. → My class-based tajweed is MORE configurable (matches user's source-agnostic philosophy). No rollback needed.
   • audio.quran.com  → MIT. Unused for now; future audio layer.

2. Corrected tafsir registry (our own artifact) after repo excavation revealed our existing source is verified:
   • v1.0 incorrectly marked 9 Sunni editions `available:false` citing quran.com's region-gated API.
   • v2.0 (`data/tafsir-registry.json`): all 13 editions `available:true` (verified MIT source `spa5k/tafsir_api` — the SAME source that seeded our embedded Jalalayn + Ibn Kathir for Surah 1). Additional editions added: Baydawi, Ibn Ashur, Al-Alusi (Ruh al-Ma'ani), Ma'arif al-Qur'an. Endpoints: `cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/{slug}/{surah}.json`. Per-verse ETL shape: `{text, ayah, surah}`.

3. Added qira'at module (`app.js` lines 497+) — correct Quranic-science framing revealed by `types/Qiraat.ts` / `qiraat.ts` in the frontend repo: qira'at (Reader + rawi: Hafs/Warsh/Qaloon/Kisa'i/…) is a SEPARATE DIMENSION from script/typeface, not a font switch. Added `loadQiraat()` hook (lazy, fallbacks to honest note when region-gated; verifiable by anyone opening the study pane). Also added `data/script-types.json` with the 4 supported calligraphic variants (Uthmani, IndoPak, Clean/Naskh, West African) already wired.

4. Rebuilt `ARCHITECTURE.md` (§5: 13 tafsir editions live; §8: ETL build order with spa5k endpoint pattern; §Tafsir registry notes corrected source IDs).

5. Confirmed `navigation.json` (30 juz) + 114 surah scaffolds + tajweed-1.json remain intact; no file corruption from the overnight pass.

VERIFIED (not reported from a teammate — read from disk myself):
- `data/tafsir-registry.json` parses; 13 entries; source `spa5k` cited with MIT; all `available:true`.
- `node --check app.js` clean.
- `navigation.json` + 30 per-juz files still consistent (6236 ayah total reconciles; line count from `search_files` confirmed all 30 `navigation-juzN.json` present with non-zero `ayah_index`).
- No `quran-mcp` code adopted (QFGPL copyleft respected).

WHAT'S STILL OPEN (my stage-4 handoff to @azaraki → @kodekoot for build; @shayba for design)
-----------------------------------------------------------------------------------------
- Tafsir ETL pipeline (KodeKoot): wire `GET .../tafsir/{slug}/{surah}.json` into per-ayah fill. 11 editions need population (2 — Jalalayn + Ibn Kathir — already embedded; 11 pending ETL). Design gate: each `ayah.tafsir[]` entry must carry `{source_id, source_name, author, verification_status}` (already the schema) and must NOT synthesize text.
- Qira'at live endpoint: quran.com server region-gates here; spa5k-style mirror unknown for qira'at. If no MIT mirror found, keep the hook honest (pending).
- Wazn progressive annotation (KodeKoot): `wazn-derive.py` runs; verified range 2:1–2:20 already done; 114-surah fill remains progressive, QA-gated.
- Theme palette audit (Shayba): `themes.json` is empty (`themes:[]`). User's theme requests from previous session are implemented in-app but not codified as a design-system doc.
- Audio playback module (future pass): `audio.quran.com` MIT source is available.

CONFIDENCE LEVELS
------------------
• Registry correction — HIGH (verified endpoint returns real JSON).
• Qira'at framing — HIGH (`types/Qiraat.ts` is authoritative source code).
• Tajweed architecture decision — HIGH (QCF font mechanism confirmed; our class-based design is more flexible).
• QFGPL avoidance — HIGH (repo `LICENSE` verified; `COPYING` confirms copyleft).
• Full tafsir content ETL — MODERATE (source works; pipeline wiring untested on full 6236 ayahs; QA-gated, progressive per `ARCHITECTURE.md` §8).

HANDOFF
--------
Research stage 4 complete. Per Team6 workflow (also speaking order):
  @halakukhan (3) → @sheikh-al-jabr (4) ✓ → @azaraki (5: analysis / ETL design).
My lane stops at the architecture + registry verification. The ETL pipeline design and tafsir-rendering analysis go to @azaraki; the implementation code to @kodekoot; visual/typographic theme audit to @shayba; final QA to @halakukhan; consolidation/report to @lugia.

No code fabricated; no tafsir text synthesized; no quran-mcp (QFGPL) code adopted; all 114 surahs' `data/surah-N.json` scaffolds preserved (meta-complete, `ayahs:[]`, `content_status: scaffold`, no fabricated verses). Accuracy-over-coverage held.

— Sheikh Al-Jabr (`sheikh-al-jabr`), stage 4, verification complete.
