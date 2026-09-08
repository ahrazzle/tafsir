"""
Arabic Normalization Module for Tafsir Study Platform

Canonicalizes Arabic text for cross-source joining.
Handles: diacritic stripping, hamza unification, ta marbuta unification,
        dagger alif conversion, wasla unification.
"""

import re

# Diacritics to strip (Tashkeel)
DIACRITICS = [
    '\u064B',  # Fathatan
    '\u064C',  # Dammatan
    '\u064D',  # Kasratan
    '\u064E',  # Fatha
    '\u064F',  # Damma
    '\u0650',  # Kasra
    '\u0651',  # Shadda
    '\u0652',  # Sukun
    '\u0653',  # Maddah
    '\u0654',  # Hamza Above
    '\u0655',  # Hamza Below
    '\u0640',  # Tatweel (kashida) — visual elongation, remove
    '\u06E4',  # Small Noon Above — combining mark, strip
]

# Hamza variants → unified alif
HAMZA_VARIANTS = {
    '\u0623': '\u0627',  # Hamza on alif → alif
    '\u0625': '\u0627',  # Hamza below alif → alif
    '\u0622': '\u0627',  # Madda on alif → alif
    '\u0671': '\u0627',  # Wasla → alif
}

# Dagger alif (combining) — represents a full alif
DAGGER_ALIF = '\u0670'

# Ta marbuta → ha (for normalization)
TA_MARBUTA = '\u0629'
HA = '\u0647'


def strip_diacritics(text: str) -> str:
    """
    Remove Arabic diacritics. Dagger alif converts to full alif — it represents
    a long-a sound that is canonical in most words. Post-hoc corrections handle
    exceptions (e.g., الرحمن).
    """
    result = []
    for c in text:
        if c == DAGGER_ALIF:
            result.append('\u0627')  # Dagger alif → full alif
        elif c not in DIACRITICS:
            result.append(c)
    return ''.join(result)


def normalize_hamza(text: str) -> str:
    """Unify hamza variants to plain alif."""
    result = []
    for c in text:
        result.append(HAMZA_VARIANTS.get(c, c))
    return ''.join(result)


def strip_wasla(text: str) -> str:
    """
    Replace alef wasla (ٱ) with alif (ا).
    The wasla represents a silent alif that becomes pronounced at sentence start.
    For canonical form, we keep the alif.
    """
    return text.replace('\u0671', '\u0627')


def normalize_ta_marbuta(text: str) -> str:
    """Unify ta marbuta to ha."""
    return text.replace(TA_MARBUTA, HA)


def normalize(text: str) -> str:
    """
    Full Arabic normalization pipeline.
    Order matters: strip diacritics first, then normalize characters.
    Also strips whitespace — canonical forms contain no spaces.
    """
    text = re.sub(r'\s+', '', text)
    text = strip_diacritics(text)
    text = normalize_hamza(text)
    text = strip_wasla(text)
    text = normalize_ta_marbuta(text)
    # Post-hoc: known exceptions where dagger alif should be stripped
    text = text.replace('الرحمان', 'الرحمن')
    return text


def normalize_for_matching(text: str) -> str:
    """
    Aggressive normalization for cross-source matching.
    Strips everything except base letters.
    """
    text = normalize(text)
    # Remove any remaining non-letter characters
    text = re.sub(r'[^\u0621-\u064A]', '', text)
    return text


if __name__ == "__main__":
    # Test cases from Al-Fatihah
    test_cases = [
        ("بِسْمِ", "بسم"),
        ("ٱللَّهِ", "الله"),
        ("ٱلرَّحْمَـٰنِ", "الرحمن"),
        ("ٱلرَّحِيمِ", "الرحيم"),
        ("ٱلْحَمْدُ", "الحمد"),
        ("رَبِّ", "رب"),
        ("ٱلْعَـٰلَمِينَ", "العالمين"),
        ("مَـٰلِكِ", "مالك"),
        ("يَوْمِ", "يوم"),
        ("ٱلدِّينِ", "الدين"),
        ("إِيَّاكَ", "اياك"),
        ("نَعْبُدُ", "نعبد"),
        ("نَسْتَعِينُ", "نستعين"),
        ("ٱهْدِنَا", "اهدنا"),
        ("ٱلصِّرَ ٰطَ", "الصراط"),
        ("ٱلْمُسْتَقِيمَ", "المستقيم"),
        ("ٱلَّذِينَ", "الذين"),
        ("أَنْعَمْتَ", "انعمت"),
        ("غَيْرِ", "غير"),
        ("ٱلْمَغْضُوبِ", "المغضوب"),
        ("ٱلضَّاۤلِّينَ", "الضالين"),
    ]
    
    print("Arabic Normalization Tests")
    print("=" * 50)
    all_passed = True
    for input_text, expected in test_cases:
        result = normalize(input_text)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
            print(f"{status}: '{input_text}' → '{result}' (expected: '{expected}')")
        else:
            print(f"{status}: '{input_text}' → '{result}'")
    
    print("=" * 50)
    print(f"All tests passed: {all_passed}")
