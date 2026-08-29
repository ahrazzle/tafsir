"""
ETL: Merge tafsir editions from spa5k into ayah.tafsir[] for Juz 1 (surahs 1-2, ayahs 2:1-141).

Per Azaraki's spec:
- Build-time script, not runtime fetch
- Iterate default_order x surahs [1, 2]
- Map source_id -> spa5k_slug
- Filter to Juz 1 range at write time
- Merge into ayah.tafsir[] with surah-1.json schema
- No fabrication, no placeholders — skip-and-log absences
"""
import json
import sys
import time
import urllib.request

BASE = "https://cdn.jsdelivr.net/gh/spa5k/tafsir_api@main/tafsir/{slug}/{surah}.json"
SURAHS = [1, 2]
JUZ1_BAQARAH_MAX = 141  # Juz 1 covers 2:1-141

# Edition order (default_order from Azaraki's spec)
# NOTE: Sa'di slug is ar-tafseer-al-saddi (registry-correct), not ar-tafsir-al-saddi.
# Tahrir slug is dead on spa5k (404) — see etl-log.json.
EDITION_ORDER = [
    "spa5k-en-al-jalalayn",
    "spa5k-en-tafisr-ibn-kathir",
    "spa5k-en-maarif",
    "spa5k-ar-tabari",
    "spa5k-ar-qurtubi",
    "spa5k-ar-saddi",
    "spa5k-ar-baghawi",
    "spa5k-ar-muyassar",
    "spa5k-en-tazkirul",
    "spa5k-en-zilal",
    "spa5k-ar-baydawi",
    "spa5k-ar-tahrir",
    "spa5k-ar-alusi",
]


def load_registry(path="data/tafsir-registry.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_surah(slug, surah):
    """Fetch a surah's tafsir for an edition. Returns list of {ayah, surah, text} or None."""
    url = BASE.format(slug=slug, surah=surah)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # Two shapes: bare list, or {ayahs: [...]}
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("ayahs"), list):
            return data["ayahs"]
        return None
    except Exception as ex:
        print(f"  FETCH ERROR {slug}/{surah}: {ex}")
        return None


def build_ayah_map(surah_file):
    """Return {verse_key: ayah_obj} for a surah data file."""
    with open(surah_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {a["verse_key"]: a for a in data["ayahs"]}, data


def main():
    registry = load_registry()
    editions = registry["editions"]
    log = {"fetched": [], "skipped": [], "gaps": [], "errors": []}

    for surah in SURAHS:
        surah_file = f"data/surah-{surah}.json"
        ayah_map, surah_data = build_ayah_map(surah_file)
        print(f"=== Surah {surah} ({len(ayah_map)} ayahs in file) ===")

        for sid in EDITION_ORDER:
            if sid not in editions:
                log["errors"].append(f"{sid}: not in registry")
                continue
            edition = editions[sid]
            slug = edition["spa5k_slug"]

            entries = fetch_surah(slug, surah)
            if entries is None:
                log["skipped"].append(f"{sid}/s{surah}: fetch failed")
                continue
            if not isinstance(entries, list) or len(entries) == 0:
                log["skipped"].append(f"{sid}/s{surah}: empty")
                continue

            # Build text-by-ayah-number lookup
            text_by_ayah = {}
            for e in entries:
                if isinstance(e, dict) and "ayah" in e and "text" in e:
                    text_by_ayah[int(e["ayah"])] = e["text"]

            # Filter to Juz 1 range: surah 1 all, surah 2 up to 141
            ayah_nums = sorted(text_by_ayah.keys())
            if surah == 2:
                ayah_nums = [n for n in ayah_nums if n <= JUZ1_BAQARAH_MAX]
            else:
                ayah_nums = [n for n in ayah_nums]

            # Contiguity check: expected range
            expected_max = JUZ1_BAQARAH_MAX if surah == 2 else len(ayah_map)
            missing = [n for n in range(1, expected_max + 1) if n not in text_by_ayah]
            if missing:
                log["gaps"].append(f"{sid}/s{surah}: missing ayahs {missing[:10]} (total {len(missing)})")

            # Merge into each ayah
            merged_count = 0
            for n in ayah_nums:
                if n not in text_by_ayah:
                    continue
                verse_key = f"{surah}:{n}"
                if verse_key not in ayah_map:
                    continue
                ayah = ayah_map[verse_key]
                # Check not already present
                if any(t["source_id"] == sid for t in ayah.get("tafsir", [])):
                    continue
                entry = {
                    "source_id": sid,
                    "source_name": edition.get("name", sid),
                    "author": edition.get("author", ""),
                    "text": text_by_ayah[n],
                    "verification_status": "sourced",
                    "complexity_level": 2,
                    "license": edition.get("license", ""),
                }
                if "tafsir" not in ayah:
                    ayah["tafsir"] = []
                ayah["tafsir"].append(entry)
                merged_count += 1

            log["fetched"].append(f"{sid}/s{surah}: {merged_count} merged")
            print(f"  {sid}: {merged_count} merged")
            time.sleep(0.2)

        # Write updated surah file
        with open(surah_file, "w", encoding="utf-8") as f:
            json.dump(surah_data, f, ensure_ascii=False, indent=2)
        print(f"  Wrote {surah_file}")

    print("\n=== LOG ===")
    for k, v in log.items():
        print(f"{k}: {len(v)}")
        for item in v[:15]:
            print(f"  {item}")

    # Save log
    with open("etl-log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print("\nLog saved to etl-log.json")


if __name__ == "__main__":
    main()
