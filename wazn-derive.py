#!/usr/bin/env python3
"""
wazn-derive.py — Progressive wazn (morphological pattern) annotation for Al-Baqarah 1-141.
Source of truth: mustafa0x/quran-morphology (Quranic Arabic Corpus v0.4).
Verified batch: 2:1-2:10 (curated by hand against classical sarf).
Everything else: algorithmically derived, marked pending.
"""
import re, json, os
from curated_batch_2 import CURATED_B2

HERE = os.path.dirname(os.path.abspath(__file__))
MORPH = os.path.join(HERE, 'baqarah-morphology.json')

# ── Standard Arabic verb patterns (classical sarf) ───────────────────────────
PERF = {'1':'فَعَلَ','2':'فَعَّلَ','3':'فَاعَلَ','4':'أَفْعَلَ','5':'تَفَعَّلَ','6':'تَفَاعَلَ',
        '7':'اِنْفَعَلَ','8':'اِفْتَعَلَ','9':'اِفْعَلَّ','10':'اِسْتَفْعَلَ'}
PERF_PASS = {'1':'فُعِلَ','2':'فُعِّلَ','3':'فُوعِلَ','4':'أُفْعِلَ','5':'تُفُعِّلَ','6':'تُفُوعِلَ',
             '7':'اُنْفُعِلَ','8':'اُفْتُعِلَ','10':'اُسْتُفْعِلَ'}
IMPF = {'1':'يَفْعَلُ','2':'يُفَعِّلُ','3':'يُفَاعِلُ','4':'يُفْعِلُ','5':'يَتَفَعَّلُ','6':'يَتَفَاعَلُ',
        '7':'يَنْفَعِلُ','8':'يَفْتَعِلُ','9':'يَفْعَلُّ','10':'يَسْتَفْعِلُ'}
IMPF1_VOWELS = {  # Form I imperfect vowel variants (known per verb)
    'قول':'يَفْعُلُ','شعر':'يَفْعُلُ','خدع':'يَفْعَلُ','كذب':'يَفْعِلُ','رزق':'يَفْعَلُ',
    'كفر':'يَفْعَلُ','ختم':'يَفْعَلُ','زيد':'يَفْعَلُ','كون':'يَفْعَلُ','نزل':'يَفْعَلُ'
}
ACT_PCPL = {'1':'فَاعِل','2':'مُفَعِّل','3':'مُفَاعِل','4':'مُفْعِل','5':'مُتَفَعِّل','6':'مُتَفَاعِل',
            '7':'مُنْفَعِل','8':'مُفْتَعِل','9':'مُفْعَلّ','10':'مُسْتَفْعِل'}
PASS_PCPL = {'1':'مَفْعُول','2':'مُفَعَّل','3':'مُفَاعَل','4':'مُفْعَل','5':'مُتَفَعَّل','6':'مُتَفَاعَل',
             '7':'مُنْفَعَل','8':'مُفْتَعَل','10':'مُسْتَفْعَل'}
IMPV = {'1':'اِفْعَلْ','2':'فَعِّلْ','3':'فَاعِلْ','4':'أَفْعِلْ','5':'تَفَعَّلْ','6':'تَفَاعَلْ',
        '7':'اِنْفَعِلْ','8':'اِفْتَعِلْ','10':'اِسْتَفْعِلْ'}

FORM_MEANING = {
    '1': 'Base form — the simple root verb in its unmodified state',
    '2': 'Intensive or causative — repetition, intensity, or making something happen',
    '3': 'Mutual action or attempt — done with another, or striving toward',
    '4': 'Causative — to make someone do something, or to enter a state',
    '5': 'Reflexive of Form II — the effect returns to the subject',
    '6': 'Reciprocal — mutual action between two parties',
    '7': 'Passive/reflexive — the action befalls the subject',
    '8': 'Acquired or selective — the subject acquires the action for itself',
    '9': 'Becoming a quality — taking on a color or characteristic',
    '10': 'Seeking or requesting — to ask for the action'
}
PCPL_ACT_MEANING = 'The one who performs the action — the active doer (اسم الفاعل)'
PCPL_PASS_MEANING = 'The one upon whom the action is done — the passive receiver (اسم المفعول)'

# ── Curated verified batch: 2:1-2:10 ─────────────────────────────────────────
# Each entry: wazn template, form description, meaning, root-in-template, examples
VERIFIED = {
    '2:2:2': ('فِعَال','Derived noun (اسم)','The classic template for written things, books, and intensives','ك-ت-ب → كِتَاب',[('جِلَاس','root ج-ل-س','sitting assembly'),('رِكَاب','root ر-ك-ب','riding, stirrups')]),
    '2:2:4': ('فَعْل','Form I verbal noun','Basic action noun — doubt, uncertainty','ر-ي-ب → رَيْب',[('شَكّ','root ش-ك-ك','doubt'),('فَهْم','root ف-ه-م','understanding')]),
    '2:2:6': ('فُعْلَى','Weak verbal noun (final weak)','Guidance — a noun of quality from a hollow/defective root','ه-د-ي → هُدًى',[('مُدًى','root م-د-ي','extent, reach'),('هُدًى','root ه-د-ي','guidance')]),
    '2:2:7': ('مُفْتَعِل','Form VIII active participle','The one who guards himself — reflexive acquisition of the meaning','و-ق-ي → مُتَّقٍ',[('مُكْتَسِب','root ك-س-ب','one who earns'),('مُجْتَهِد','root ج-ه-د','one who strives')]),
    '2:3:2': ('يُفْعِلُ','Form IV imperfect verb','He makes/brings to faith — causative imperfect','أ-م-ن → يُؤْمِنُ',[('يُكْرِمُ','root ك-ر-م','he honors'),('يُعْلِمُ','root ع-ل-م','he informs')]),
    '2:3:3': ('فَعْل','Form I verbal noun','What is hidden — the unseen','غ-ي-ب → غَيْب',[('فَيْض','root ف-ي-ض','overflow'),('كَيْد','root ك-ي-د','scheming')]),
    '2:3:4': ('يُفْعِلُ','Form IV imperfect verb (hollow)','He establishes, makes upright — causative of standing','ق-و-م → يُقِيمُ',[('يُعِيدُ','root ع-و-د','he returns'),('يُقِيمُ','root ق-و-م','he establishes')]),
    '2:3:5': ('فَعَلَة','Feminine verbal noun','The ritual prayer — feminine noun from the root of connection','ص-ل-و → صَلَاة',[('زَكَاة','root ز-ك-و','purification, alms'),('نَجَاة','root ن-ج-و','salvation')]),
    '2:3:7': ('فَعَلَ','Form I perfect verb','He provided — base perfect','ر-ز-ق → رَزَقَ',[('كَتَبَ','root ك-ت-ب','he wrote'),('جَلَسَ','root ج-ل-س','he sat')]),
    '2:3:8': ('يُفْعِلُ','Form IV imperfect verb','He spends — causative imperfect of going out','ن-ف-ق → يُنْفِقُ',[('يُخْرِجُ','root خ-ر-ج','he brings out'),('يُدْخِلُ','root د-خ-ل','he brings in')]),
    '2:4:4': ('أُفْعِلَ','Form IV perfect passive','It was sent down — passive causative','ن-ز-ل → أُنْزِلَ',[('أُكْرِمَ','root ك-ر-م','he was honored'),('أُنْقِذَ','root ن-ق-ذ','he was rescued')]),
    '2:4:9': ('فَعْل','Form I verbal noun','Before — noun of time/place from precedence','ق-ب-ل → قَبْل',[('بَعْد','root ب-ع-د','after'),('فَوْق','root ف-و-ق','above')]),
    '2:4:10': ('فَاعِلَة','Form I feminine active participle','The last — feminine of the active doer','أ-خ-ر → آخِرَة',[('سَابِقَة','root س-ب-ق','preceding one'),('كَامِلَة','root ك-م-ل','complete one')]),
    '2:4:12': ('يُفْعِلُ','Form IV imperfect verb','He is certain — causative of certainty','ي-ق-ن → يُوقِنُ',[('يُعْلِنُ','root ع-ل-ن','he declares'),('يُؤْمِنُ','root أ-م-ن','he believes')]),
    '2:4:2': ('يُفْعِلُ','Form IV imperfect verb','He makes/brings to faith — causative imperfect','أ-م-ن → يُؤْمِنُ',[('يُكْرِمُ','root ك-ر-م','he honors'),('يُعْلِمُ','root ع-ل-م','he informs')]),
    '2:4:7': ('أُفْعِلَ','Form IV perfect passive','It was sent down — passive causative','ن-ز-ل → أُنْزِلَ',[('أُكْرِمَ','root ك-ر-م','he was honored'),('أُنْقِذَ','root ن-ق-ذ','he was rescued')]),
    '2:6:11': ('يُفْعِلُ','Form IV imperfect verb','He makes/brings to faith — causative imperfect','أ-م-ن → يُؤْمِنُ',[('يُكْرِمُ','root ك-ر-م','he honors'),('يُعْلِمُ','root ع-ل-م','he informs')]),
    '2:7:2': ('-','Proper noun','The divine name Allāh — no derivational pattern; a unique proper noun','—',[]),
    '2:8:6': ('-','Proper noun','The divine name Allāh — no derivational pattern','—',[]),
    '2:9:2': ('-','Proper noun','The divine name Allāh — no derivational pattern','—',[]),
    '2:10:5': ('-','Proper noun','The divine name Allāh — no derivational pattern','—',[]),
    '2:5:3': ('فُعْلَى','Weak verbal noun','Guidance','ه-د-ي → هُدًى',[('مُدًى','root م-د-ي','extent'),('هُدًى','root ه-د-ي','guidance')]),
    '2:5:5': ('فَعْل','Form I noun (geminate)','Lord, nurturer — the one who raises and sustains','ر-ب-ب → رَبّ',[('سَيِّد','root س-و-د','master'),('حَقّ','root ح-ق-ق','truth')]),
    '2:5:8': ('مُفْعِل','Form IV active participle','The one who succeeds — causative doer','ف-ل-ح → مُفْلِح',[('مُحْسِن','root ح-س-ن','one who does good'),('مُكْرِم','root ك-ر-م','one who honors')]),
    '2:6:3': ('فَعَلَ','Form I perfect verb','They disbelieved — base perfect','ك-ف-ر → كَفَرَ',[('كَتَبَ','root ك-ت-ب','he wrote'),('جَحَدَ','root ج-ح-د','he denied')]),
    '2:6:4': ('فَعَال','Form I noun','The same — noun of equality','س-و-ي → سَوَاء',[('جَمَال','root ج-م-ل','beauty'),('سَلَام','root س-ل-م','peace')]),
    '2:6:6': ('أَفْعَلَ','Form IV perfect verb','Did you warn — causative perfect with interrogative','ن-ذ-ر → أَنْذَرَ',[('أَنْزَلَ','root ن-ز-ل','he sent down'),('أَكْرَمَ','root ك-ر-م','he honored')]),
    '2:6:9': ('يُفْعِلُ','Form IV imperfect verb (jussive)','You warn — causative imperfect','ن-ذ-ر → تُنْذِرُ',[('يُنْزِلُ','root ن-ز-ل','he sends down'),('يُكْرِمُ','root ك-ر-م','he honors')]),
    '2:7:1': ('فَعَلَ','Form I perfect verb','He sealed — base perfect','خ-ت-م → خَتَمَ',[('كَتَبَ','root ك-ت-ب','he wrote'),('فَتَحَ','root ف-ت-ح','he opened')]),
    '2:7:4': ('فُعُول','Plural noun','Hearts — broken plural','ق-ل-ب → قُلُوب',[('عُيُون','root ع-ي-ن','eyes'),('نُفُوس','root ن-ف-س','souls')]),
    '2:7:6': ('فَعْل','Form I verbal noun','Hearing — base noun','س-م-ع → سَمْع',[('عَقْل','root ع-ق-ل','intellect'),('عِلْم','root ع-ل-م','knowledge')]),
    '2:7:8': ('أَفْعَال','Broken plural','Sights — plural of فَعْل','ب-ص-ر → أَبْصَار',[('أَقْلَام','root ق-ل-م','pens'),('أَزْمَان','root ز-م-ن','times')]),
    '2:7:9': ('فِعَالَة','Form I noun','A covering — noun of instrument/instance','غ-ش-و → غِشَاوَة',[('عِبَادَة','root ع-ب-د','worship'),('كِتَابَة','root ك-ت-ب','writing')]),
    '2:7:11': ('فَعَال','Form I noun','Punishment — noun of the concept','ع-ذ-ب → عَذَاب',[('سَلَام','root س-ل-م','peace'),('جَمَال','root ج-م-ل','beauty')]),
    '2:7:12': ('فَعِيل','Form I adjective (intensive)','Mighty — intensive adjective','ع-ظ-م → عَظِيم',[('كَرِيم','root ك-ر-م','generous'),('حَكِيم','root ح-ك-م','wise')]),
    '2:8:2': ('فَعَال','Form I noun','The people — from the root of sociability','أ-ن-س → نَاس',[('سَلَام','root س-ل-م','peace'),('جَمَال','root ج-م-ل','beauty')]),
    '2:8:4': ('يَفْعُلُ','Form I imperfect verb (hollow)','He says — base imperfect of utterance','ق-و-ل → يَقُولُ',[('يَقُومُ','root ق-و-م','he stands'),('يَخُوضُ','root خ-و-ض','he wades')]),
    '2:8:5': ('أَفْعَلَ','Form IV perfect verb (hamzated)','We believed — causative perfect','أ-م-ن → آمَنَّا',[('أَنْزَلْنَا','root ن-ز-ل','we sent down'),('أَكْرَمْنَا','root ك-ر-م','we honored')]),
    '2:8:7': ('فَعْل','Form I noun','Day — base noun of time','ي-و-م → يَوْم',[('لَيْل','root ل-ي-ل','night'),('حِين','root ح-ي-ن','time')]),
    '2:8:8': ('فَاعِل','Form I active participle','The last — active doer','أ-خ-ر → آخِر',[('سَابِق','root س-ب-ق','preceding'),('كَامِل','root ك-م-ل','complete')]),
    '2:8:11': ('مُفْعِل','Form IV active participle','Believers — causative doers','أ-م-ن → مُؤْمِن',[('مُحْسِن','root ح-س-ن','doers of good'),('مُخْلِص','root خ-ل-ص','sincere ones')]),
    '2:9:1': ('يُفَاعِلُ','Form III imperfect verb','They deceive — mutual action imperfect','خ-د-ع → يُخَادِعُ',[('يُجَادِلُ','root ج-د-ل','he argues'),('يُكَاتِبُ','root ك-ت-ب','he corresponds')]),
    '2:9:4': ('أَفْعَلَ','Form IV perfect verb','They believed','أ-م-ن → آمَنُوا',[('أَنْزَلُوا','root ن-ز-ل','they sent down'),('أَحْسَنُوا','root ح-س-ن','they did good')]),
    '2:9:6': ('يَفْعَلُ','Form I imperfect verb','They deceive — base imperfect','خ-د-ع → يَخْدَعُ',[('يَفْتَحُ','root ف-ت-ح','he opens'),('يَكْتُبُ','root ك-ت-ب','he writes')]),
    '2:9:8': ('أَفْعُل','Broken plural','Selves — broken plural','ن-ف-س → أَنْفُس',[('أَبْحُر','root ب-ح-ر','seas'),('أَذْرُع','root ذ-ر-ع','arms')]),
    '2:9:10': ('يَفْعُلُ','Form I imperfect verb','They perceive — base imperfect','ش-ع-ر → يَشْعُرُ',[('يَقُولُ','root ق-و-ل','he says'),('يَخْرُجُ','root خ-ر-ج','he goes out')]),
    '2:10:2': ('فُعُول','Broken plural','Hearts','ق-ل-ب → قُلُوب',[('عُيُون','root ع-ي-ن','eyes'),('نُفُوس','root ن-ف-س','souls')]),
    '2:10:3': ('فَعَل','Form I noun','Sickness — base noun of condition','م-ر-ض → مَرَض',[('شَرَف','root ش-ر-ف','honor'),('طَلَب','root ط-ل-ب','seeking')]),
    '2:10:4': ('فَعَلَ','Form I perfect verb (hollow)','He increased — base perfect','ز-ي-د → زَادَ',[('قَالَ','root ق-و-ل','he said'),('كَانَ','root ك-و-ن','he was')]),
    '2:10:6': ('فَعَل','Form I noun','Sickness','م-ر-ض → مَرَض',[('شَرَف','root ش-ر-ف','honor'),('طَلَب','root ط-ل-ب','seeking')]),
    '2:10:8': ('فَعَال','Form I noun','Punishment','ع-ذ-ب → عَذَاب',[('سَلَام','root س-ل-م','peace'),('جَمَال','root ج-م-ل','beauty')]),
    '2:10:9': ('فَعِيل','Form I adjective (intensive)','Painful — intensive adjective','أ-ل-م → أَلِيم',[('كَرِيم','root ك-ر-م','generous'),('عَلِيم','root ع-ل-م','all-knowing')]),
    '2:10:11': ('فَعَلَ','Form I perfect verb (hollow)','They were — base perfect of being','ك-و-ن → كَانُوا',[('قَالُوا','root ق-و-ل','they said'),('زَادُوا','root ز-ي-د','they increased')]),
    '2:10:12': ('يَفْعِلُ','Form I imperfect verb','They lie — base imperfect','ك-ذ-ب → يَكْذِبُ',[('يَضْرِبُ','root ض-ر-ب','he strikes'),('يَجْلِسُ','root ج-ل-س','he sits')]),
}

def load_morph():
    with open(MORPH) as f:
        return json.load(f)

def has(feats_list, pat):
    return any(re.search(pat, f) for f in feats_list)

def vowel_after(lemma, idx):
    """Return the combining diacritic (fatha/kasra/damma) immediately after lemma[idx], or None."""
    if idx + 1 >= len(lemma):
        return None
    ch = lemma[idx + 1]
    if ch == '\u064e':
        return 'fatha'
    if ch == '\u0650':
        return 'kasra'
    if ch == '\u064f':
        return 'damma'
    return None

def plain(s):
    return ''.join(c for c in s if not ('\u064b' <= c <= '\u0652') and c not in '\u0670\u0653\u0654\u0655\u0656\u0657\u0658\u0659\u065a\u065b\u065c\u065d\u065e')

PREFIXES = ('ال', 'و', 'ف', 'ب', 'ل', 'ك', 'س')
# suffix set for the 4-letter shape family (ون/ين/ات/ان/ة…) — anything else makes len>4
SUFFIXES = ('ون', 'ين', 'ان', 'ات', 'هما', 'هم', 'هن', 'كم', 'كن', 'نا', 'ها', 'ه', 'ة', 'ي')

def surface_core(w):
    """De-cliticized surface token (plain letters). Returns '' if irreducible."""
    tok = plain(w['full_token'])
    changed = True
    while changed:
        changed = False
        for p in PREFIXES:
            if tok.startswith(p) and len(tok) > len(p):
                tok = tok[len(p):]
                changed = True
                break
        for s in SUFFIXES:
            if tok.endswith(s) and len(tok) > len(s):
                tok = tok[:-len(s)]
                changed = True
                break
    return tok

def concords(w, lemma):
    """True if the plain lemma appears as a contiguous span inside the de-ال'd surface.
    Broken plurals (شُهَدَاء vs lemma شَهِيد) fail this; clitic-laden forms (بِٱلْكَٰفِرِينَ
    contains كافر) pass. No blind letter-stripping — ك/ب/ل etc. are legitimate root letters."""
    tok = plain(w['full_token'])
    while tok.startswith('ال'):
        tok = tok[2:]
    return lemma in tok

def shape_pattern(w):
    """
    Surface-truthful pattern detection from surface shape + root letters + voweling.
    Only claims the TEMPLATE (deterministic from surface), never the function.

    Safety rules:
    - Surface core and lemma must CONCORD (broken plurals differ — شُهَدَاء vs lemma
      شَهِيد — and get rejected, staying manual).
    - Only the 4-letter family (فَاعِل/فَعِيل/فَعُول/فِعَال/فَعَال) is claimed;
      anything longer is plural/derived territory and stays null.
    - Lemma must not carry prefixes (first letter == root[0]).
    """
    root = w['roots'][0] if w['roots'] else None
    if not root or len(root) != 3:
        return None
    lemma_raw = w['lemmas'][0] if w['lemmas'] else ''
    lemma = plain(lemma_raw)
    if lemma.startswith('ال'):
        lemma = lemma[2:]
    if len(lemma) < 4 or lemma[0] != root[0]:
        return None
    # SURFACE CONCORDANCE GUARD — the surface must contain the lemma as-is
    # (broken plurals differ from their singular lemmas and get rejected, staying manual)
    if not concords(w, lemma):
        return None
    r1, r2, r3 = root[0], root[1], root[2]
    # فَاعِل (CāCiC): ك-ت-ب → كَاتِب  [unique letter sequence]
    if lemma == r1 + 'ا' + r2 + r3:
        return ('فَاعِل', 'Form I active participle / adjective shape (اسم فاعل / صفة)')
    # فَعِيل (CaCīC): ع-ل-م → عَلِيم  [unique letter sequence]
    if lemma == r1 + r2 + 'ي' + r3:
        return ('فَعِيل', 'Form I intensive adjective shape (صفة مشبهة)')
    # فَعُول (CaCūC): ش-ك-ر → شَكُور  [unique letter sequence]
    if lemma == r1 + r2 + 'و' + r3:
        return ('فَعُول', 'Form I intensive adjective shape (صفة مشبهة)')
    # فِعَال vs فَعَال (CiCāC / CaCāC): ك-ت-ب → كِتَاب / س-ل-م → سَلَام
    if lemma == r1 + r2 + 'ا' + r3:
        v = vowel_after(lemma_raw, 0)
        if v == 'kasra':
            return ('فِعَال', 'Form I noun/adjective shape (اسم/صفة)')
        if v == 'fatha':
            return ('فَعَال', 'Form I noun/adjective shape (اسم/صفة)')
        return None
    return None

def derive_auto(w):
    """Algorithmic derivation for non-curated words. Returns entry dict (pending)."""
    feats = '|'.join(w['feats'])
    vf = None
    m = re.search(r'VF:(\d+)', feats)
    if m: vf = m.group(1)
    root = w['roots'][0] if w['roots'] else None
    pos_n = 'N' in w['pos_tags'] or 'ADJ' in w['pos_tags']

    entry = {
        'location': None, 'arabic': w['full_token'],
        'root': root, 'verification_status': 'pending',
        'wazn': None, 'wazn_arabic': None, 'wazn_form': None,
        'wazn_meaning': None, 'root_in_template': None, 'wazn_examples': []
    }
    if not vf:
        if not root:
            entry['wazn_meaning'] = 'Grammatical particle or pronoun — no lexical root'
        # Shape-derived pattern: surface + root are enough to verify the TEMPLATE,
        # even when the corpus lacks a derivation tag (e.g. كافِر tagged N only).
        # Pattern is surface-truthful; function (participle vs adjective) stays pending.
        shape = shape_pattern(w)
        if shape:
            pat, form_desc = shape
            entry.update(wazn=pat, wazn_arabic=pat, wazn_form=form_desc,
                         wazn_meaning='Template verified from surface form and root; grammatical function awaiting manual confirmation',
                         wazn_note='pattern surface-derived, function pending')
        return entry

    if has(w['feats'], r'ACT_PCPL'):
        pat = ACT_PCPL.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} active participle',
                     wazn_meaning=PCPL_ACT_MEANING)
    elif has(w['feats'], r'PASS_PCPL'):
        pat = PASS_PCPL.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} passive participle',
                     wazn_meaning=PCPL_PASS_MEANING)
    elif has(w['feats'], r'\bPASS\b'):
        pat = PERF_PASS.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} perfect passive verb',
                     wazn_meaning=FORM_MEANING.get(vf, ''))
    elif has(w['feats'], r'\bVN\b'):
        # Verbal nouns: pattern varies by root class — never guess. Pending, no pattern.
        entry.update(wazn=None, wazn_arabic=None,
                     wazn_form='Verbal noun (مصدر)',
                     wazn_meaning='Action noun derived from the verb — its pattern depends on the root class (weak, geminate, hamzated); awaiting manual verification')
    elif has(w['feats'], r'IMPV'):
        pat = IMPV.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} imperative verb',
                     wazn_meaning='Command form — directs the action to be done')
    elif has(w['feats'], r'IMPF'):
        if vf == '1':
            pat = IMPF1_VOWELS.get(root, 'يَفْعَلُ')
        else:
            pat = IMPF.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} imperfect verb',
                     wazn_meaning=FORM_MEANING.get(vf, ''))
    elif has(w['feats'], r'PERF'):
        pat = PERF.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} perfect verb',
                     wazn_meaning=FORM_MEANING.get(vf, ''))
    else:
        pat = PERF.get(vf)
        entry.update(wazn=pat, wazn_arabic=pat, wazn_form=f'Form {vf} verb',
                     wazn_meaning=FORM_MEANING.get(vf, ''))
    if root and entry['wazn_arabic']:
        entry['root_in_template'] = f"{'-'.join(root)} → {entry['wazn_arabic']}"
    return entry

def in_verified_range(k):
    try:
        surah, ayah, wpos = k.split(':')
        return surah == '2' and 1 <= int(ayah) <= 20
    except Exception:
        return False

def main():
    words = load_morph()
    # Merge batch 2 (2:11-2:20) into the verified set
    VERIFIED.update(CURATED_B2)
    result = {'meta': {}, 'words': {}}
    result['meta'] = {
        'description': 'Progressive wazn annotation for Al-Baqarah 1-141 (Juz 1). Verified batches curated by hand: 2:1-2:20. Remaining entries algorithmically derived from corpus morphology, pending verification.',
        'surah': 2, 'surah_name': 'Al-Baqarah',
        'verification_status': 'progressive',
        'verified_range': '2:1-2:20',
        'source_morphology': 'Quranic Arabic Corpus v0.4 (mustafa0x/quran-morphology)',
        'source_license': 'Corpus data CC BY-NC — attribution required',
        'method': 'Deterministic wazn derivation from corpus VF/PCPL/PASS/IMPF features + hand-curated verified batch'
    }
    for k, w in words.items():
        if k in VERIFIED:
            curated = VERIFIED[k]
            if curated[0] == '-':
                # proper noun — null wazn
                result['words'][k] = {
                    'location': k, 'arabic': w['full_token'],
                    'root': w['roots'][0] if w['roots'] else None,
                    'verification_status': 'verified',
                    'wazn': None, 'wazn_arabic': None,
                    'wazn_form': curated[1], 'wazn_meaning': curated[2],
                    'root_in_template': None, 'wazn_examples': []
                }
                continue
            wazn, form, meaning, template, examples = curated
            root = w['roots'][0] if w['roots'] else None
            result['words'][k] = {
                'location': k, 'arabic': w['full_token'],
                'root': root, 'verification_status': 'verified',
                'wazn': wazn, 'wazn_arabic': wazn, 'wazn_form': form,
                'wazn_meaning': meaning, 'root_in_template': template,
                'wazn_examples': [{'word': e[0], 'root': e[1], 'meaning': e[2]} for e in examples]
            }
        else:
            entry = derive_auto(w)
            entry['location'] = k
            # Words in the curated range are verified by inclusion — particles/pronouns
            # verified null-root entries, algorithmically derived verbs stay pending
            if in_verified_range(k) and not w['roots'] and not w['wf']:
                entry['verification_status'] = 'verified'
            result['words'][k] = entry

    v = sum(1 for e in result['words'].values() if e['verification_status'] == 'verified')
    p = sum(1 for e in result['words'].values() if e['verification_status'] == 'pending')
    d = sum(1 for e in result['words'].values() if e['wazn'])
    result['meta']['counts'] = {'verified': v, 'pending': p, 'with_wazn': d, 'total': len(result['words'])}

    out = os.path.join(HERE, 'data', 'wazn-baqarah.json')
    with open(out, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(f"Wrote {out}")
    print(f"Total: {len(result['words'])} | verified: {v} | pending: {p} | with wazn: {d}")

if __name__ == '__main__':
    main()