#!/usr/bin/env python3
"""
tajweed-tokenizer.py — Produce tajweed token data for surahs 2-3 (Juz 1-3).

Same conservative discipline as the curated tajweed-1.json sample:
  - only UNAMBIGUOUS tajweed rules are marked
  - uncertain positions are left uncoloured ('none')
  - no letter is coloured on a guessed rule

Rules implemented (deterministic from quran.com Uthmani orthography):
  ghunnah  — shadda (U+0651) on nun (ن) or mim (م)
  madd     — U+06E5 small high madda (madd waw/yaa), tatweel+superscript
             alif (ـٰ = U+0640 U+0670) which encodes madd alif, and U+0622 آ
             when present
  qalqalah — qalqalah letters (ق ط ب ج د) with sukoon (U+06E1) or shadda
  silent   — waslah alif (ٱ U+0671)
  idgham/ikhfa — left unmarked (need verified pass)

Tokenisation: split into letters with attached diacritics; tatweel and
superscript alif are kept attached to their base letter.
"""
import json, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')

SHADDA = '\u0651'
SUKOON = '\u06e1'   # small high zigzag (quran.com)
MADDA_SMALL = '\u06e5'  # small high madda (madd waw/yaa)
SUP_ALIF = '\u0670'
TATWEEL = '\u0640'
WASLA = '\u0671'
QALQALAH = set('قطبجد')

def split_letters(text):
    letters = []
    buf = ''
    for ch in text:
        if ch == ' ':
            if buf:
                letters.append(buf)
                buf = ''
            letters.append(' ')  # preserve word spaces as tokens
            continue
        # Diacritics + typographic joiners attach to the current base letter.
        # Hair space (U+200A) and word joiner (U+2060) are positional aids in the
        # Uthmani orthography — keeping them glued to their base avoids orphaned
        # marks (e.g. ذَٰ renders as ذَ + ٰ as separate tokens otherwise).
        if ('\u064b' <= ch <= '\u065f') or ch in '\u0670\u06e1\u06e5\u06e6\u0640' or ch in '\u200a\u2060':
            buf += ch
        else:
            if buf:
                letters.append(buf)
            buf = ch
    if buf:
        letters.append(buf)
    return letters

def tokenize_ayah(text):
    letters = split_letters(text)
    tokens = []
    n = len(letters)
    for i, letter in enumerate(letters):
        base = letter[0]
        has_shadda = SHADDA in letter
        has_sukoon = SUKOON in letter
        has_madda_small = MADDA_SMALL in letter
        has_sup_alif = SUP_ALIF in letter
        has_tatweel = TATWEEL in letter
        rule = 'none'
        # ghunnah: shadda on nun/mim
        if has_shadda and base in 'نم':
            rule = 'ghunnah'
        # madd: small madda on waw/yaa; any letter carrying the superscript
        # alif (ـٰ, e.g. مَـٰ in رَحْمَـٰن, وٰ in وَٰلِد) is a madd alif; U+0622
        elif has_madda_small and base in 'اوي':
            rule = 'madd'
        elif has_sup_alif:
            rule = 'madd'
        elif base == 'آ':
            rule = 'madd'
        # qalqalah: sukoon/shadda on qalqalah letter
        elif (has_sukoon or has_shadda) and base in QALQALAH:
            rule = 'qalqalah'
        # silent: waslah alif
        elif base == 'ٱ':
            rule = 'silent'
        tokens.append({'c': letter, 'r': rule})
    return tokens

def main():
    for num, name in [(2, 'Al-Baqarah'), (3, "Aal-i-Imraan")]:
        with open(os.path.join(DATA, f'surah-{num}.json')) as f:
            data = json.load(f)
        result = {
            'meta': {
                'surah': num,
                'surah_name': name,
                'scheme': 'madani',
                'verified_by': 'conservative automated tokenizer — ghunnah (shadda on ن/م), madd (U+06E5 small madda, tatweel+superscript alif, آ), qalqalah (sukoon/shadda on قطبجد), silent (waslah ٱ). Idgham/ikhfa left unmarked pending verified pass.',
                'coverage': f'letter-level for {len(data["ayahs"])} ayahs',
                'note': 'Automated from quran.com Uthmani orthography with the same conservative discipline as tajweed-1.json.'
            },
            'ayahs': {}
        }
        for a in data['ayahs']:
            result['ayahs'][a['verse_key']] = tokenize_ayah(a['arabic'])
        out = os.path.join(DATA, f'tajweed-{num}.json')
        with open(out, 'w') as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        rules = Counter()
        for vk, toks in result['ayahs'].items():
            for t in toks:
                rules[t['r']] += 1
        print(f'tajweed-{num}.json: {len(result["ayahs"])} ayahs | rules: {dict(rules)}')
        sample = result['ayahs'].get('2:1') or result['ayahs'].get('3:1')
        print('  sample:', json.dumps(sample[:6], ensure_ascii=False))

if __name__ == '__main__':
    main()
