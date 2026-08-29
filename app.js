// ═══════════════════════════════════════════════════════════════════
// Tafsir Study — application logic
// Features: Quran-wide nav (30 juz / 114 surah / 604 pages),
//   tajweed colour coding (switchable styles), script-type switching,
//   UI / script / tajweed colour themes, multi-edition Sunni tafsir.
// Convention: verse_key is the atomic join key. Accuracy over coverage.
// ═══════════════════════════════════════════════════════════════════

'use strict';

// ─── Configuration ────────────────────────────────────────────────
// Tajweed rule → CSS class. Two established colour conventions are switchable.
const TAJWEED_STYLES = {
  madani: {
    label: 'Madani (Madinah Mushaf)',
    rules: {
      madd:     'tj-madd',      // red    — prolongation
      ghunnah:  'tj-ghunnah',   // green  — nasalization
      idgham:   'tj-idgham',    // blue   — assimilation (light)
      ikhfa:    'tj-ikhfa',     // blue   — concealment
      silent:   'tj-silent',    // grey   — written, unpronounced
      qalqalah: 'tj-qalqalah'   // blue echo — bounce
    }
  },
  aalim: {
    label: 'Aalim (colour-coded learner)',
    rules: {
      madd:     'tj-madd',      // yellow — madd asli (2-count)
      ghunnah:  'tj-ghunnah',   // green
      idgham:   'tj-idgham',    // light blue
      ikhfa:    'tj-ikhfa',     // light blue
      silent:   'tj-silent',    // grey
      qalqalah: 'tj-qalqalah'   // blue echo
    }
  }
};

// Script / typeface options. The rasm (Hafs text) is identical; only the
// calligraphic typeface differs. Fonts loaded from Google Fonts CDN.
const SCRIPT_OPTIONS = {
  uthmani: { label: 'Uthmani (Madinah)', font: "'Amiri', 'Scheherazade New', serif", load: 'Amiri:wght@400;700&family=Scheherazade+New:wght@400;700' },
  indopak: { label: 'IndoPak (South Asian)', font: "'Lateef', serif", load: 'Lateef:wght@400;700' },
  clean:   { label: 'Clean (Noto Naskh)', font: "'Noto Naskh Arabic', serif", load: 'Noto+Naskh+Arabic:wght@400;700' },
  maghribi:{ label: 'West African (Qalam)', font: "'Aref Ruqaa', serif", load: 'Aref+Ruqaa:wght@400;700' }
};

// Qira'at (variant readings) — the Quranically-correct framing for what the UI
// calls "script". The rasm is fixed (Hafs an-Asim is our base text); the qira'at
// are the ten authenticated reading traditions. quran.com models them as
// Reader + Transmitter (rawi). Source: github.com/quran/quran.com-frontend-next
// types/Qiraat.ts + StudyModeQiraatTab. The public QDC qira'at matrix API
// (api.quran.com/api/qdc/qiraat/matrix/by_verse/{verseKey}) is region-gated from
// this environment, so this is a documented fetch hook — it renders real variant
// text when reachable, otherwise an honest "not available from this network" note.
// "script" (typeface) and "qira'at" (reading) are deliberately SEPARATE dimensions.
const QIRAAT_READERS = {
  hafs_an_asim:   { label: 'Hafs (an-Asim)', transmitter: 'via Shu’bah / Hafs', base: true },
  warsh_an_nafi:  { label: 'Warsh (an-Nafi’)' },
  qaloon_an_nafi: { label: 'Qaloon (an-Nafi’)' },
  adoori_an_kisaai: { label: 'Ad-Doori (al-Kisa’i)' },
  assoos_an_kisaai: { label: 'As-Soosi (al-Kisa’i)' },
  khalaf_an_hamza:{ label: 'Khalaf (Hamzah)' },
  khallad_an_hamza:{ label: 'Khallad (Hamzah)' },
  hafs_ad_duri:   { label: 'Hafs (ad-Doori)' },
  abu_amr_basri:  { label: 'Abu ‘Amr (al-Basri)' },
  ibn_amir_shami: { label: 'Ibn ‘Amir (ash-Shami)' }
};
const QIRAAT_CARD_COLORS = { white:'#FFFFFF', green:'#B7D7A8', pink:'#EA9999', blue:'#A4C2F4' };
async function loadQiraat(verseKey) {
  // Hook: try the documented QDC endpoint; return null on failure (region-gate).
  try {
    const r = await fetch(`https://api.quran.com/api/qdc/qiraat/matrix/by_verse/${encodeURIComponent(verseKey)}?language=en`);
    if (!r.ok) return null;
    const d = await r.json();
    return d.junctures || null;
  } catch (e) { return null; }
}

// Themes layer (Level 3 / Explore): loads data/themes.json once, caches it.
// Each entry: { verse_key, theme, description }. Never fabricates content.
let themesData = null;
async function loadThemes() {
  if (themesData) return themesData;
  try {
    const r = await fetch('data/themes.json');
    if (!r.ok) return null;
    themesData = await r.json();
    return themesData;
  } catch (e) { return null; }
}

// UI themes — set CSS custom properties on <html data-theme>.
const THEMES = {
  classic: { label: 'Classic (parchment + green)', dark: false },
  sepia:   { label: 'Sepia', dark: false },
  olive:   { label: 'Olive', dark: false },
  midnight:{ label: 'Midnight (dark)', dark: true },
  royal:   { label: 'Royal (navy + gold)', dark: false }
};

// Script ink (Arabic text) colour themes.
const INK_THEMES = {
  ink:    { label: 'Classic black', var: 'var(--ink)' },
  sepia:  { label: 'Sepia brown', var: '#5b3a29' },
  green:  { label: 'Green', var: 'var(--accent-ink)' },
  navy:   { label: 'Navy', var: '#1f2d4d' },
  maroon: { label: 'Maroon', var: '#6b2737' }
};

// ─── State ────────────────────────────────────────────────────────
let NAV = null;
let currentJuz = 1;
let currentSurah = 1;
let currentPage = null;
let loadedData = {};
let currentWord = null;
let currentAyah = null;
let isPaneOpen = false;
let selectedTafsirIndex = 0;
let tafsirRegistry = null;
let tajweedCache = {};   // surah -> {ayahs:{verse_key:[tokens]}}

const settings = {
  tajweed: false,
  tajweedStyle: 'madani',
  script: 'uthmani',
  theme: 'classic',
  ink: 'ink'
};

// ─── DOM ──────────────────────────────────────────────────────────
const juzSelect = document.getElementById('juzSelect');
const surahSelect = document.getElementById('surahSelect');
const pageSelect = document.getElementById('pageSelect');
const verseList = document.getElementById('verseList');
const statusEl = document.getElementById('status');
const studyPane = document.getElementById('studyPane');
const overlay = document.getElementById('overlay');
const studyArabic = document.getElementById('studyArabic');
const studyTranslation = document.getElementById('studyTranslation');
const studyLocation = document.getElementById('studyLocation');
const studyContent = document.getElementById('studyContent');
const tafsirSelect = document.getElementById('tafsirSelect');
const paneHandle = document.getElementById('paneHandle');
// settings controls
const tajweedToggle = document.getElementById('tajweedToggle');
const tajweedStyleSel = document.getElementById('tajweedStyle');
const scriptSel = document.getElementById('scriptSelect');
const themeSel = document.getElementById('themeSelect');
const inkSel = document.getElementById('inkSelect');

// ─── Persistence (localStorage, best-effort) ────────────────────────
function saveSettings() {
  try { localStorage.setItem('tafsir-settings', JSON.stringify(settings)); } catch (e) {}
}
function loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem('tafsir-settings'));
    if (s) Object.assign(settings, s);
  } catch (e) {}
}

// ─── Populate selectors (juz-aware, global) ──────────────────────────
function populateSettingsControls() {
  // tajweed style
  tajweedStyleSel.innerHTML = '';
  Object.keys(TAJWEED_STYLES).forEach(k => {
    const o = new Option(TAJWEED_STYLES[k].label, k);
    tajweedStyleSel.appendChild(o);
  });
  tajweedStyleSel.value = settings.tajweedStyle;
  tajweedStyleSel.disabled = !settings.tajweed;
  // script
  scriptSel.innerHTML = '';
  Object.keys(SCRIPT_OPTIONS).forEach(k => {
    scriptSel.appendChild(new Option(SCRIPT_OPTIONS[k].label, k));
  });
  scriptSel.value = settings.script;
  // theme
  themeSel.innerHTML = '';
  Object.keys(THEMES).forEach(k => themeSel.appendChild(new Option(THEMES[k].label, k)));
  themeSel.value = settings.theme;
  // ink
  inkSel.innerHTML = '';
  Object.keys(INK_THEMES).forEach(k => inkSel.appendChild(new Option(INK_THEMES[k].label, k)));
  inkSel.value = settings.ink;
  // toggle
  tajweedToggle.checked = settings.tajweed;
}

function applyTheme() {
  const root = document.documentElement;
  root.setAttribute('data-theme', settings.theme);
  // ink theme applies via a CSS var on :root
  root.style.setProperty('--ink-arabic', INK_THEMES[settings.ink].var);
  // preload script font if needed
  const f = SCRIPT_OPTIONS[settings.script].load;
  let link = document.getElementById('dynamic-font');
  if (!link) {
    link = document.createElement('link');
    link.id = 'dynamic-font';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }
  link.href = `https://fonts.googleapis.com/css2?family=${f}&display=swap`;
  root.setAttribute('data-script', settings.script);
  saveSettings();
}

function populateJuzSelect() {
  juzSelect.innerHTML = '';
  Object.keys(NAV.juz).forEach(num => {
    const j = NAV.juz[num];
    const opt = document.createElement('option');
    opt.value = num;
    const ready = j.surahs.some(s => NAV.surahs[s].content);
    opt.textContent = `Juz ${num}${ready ? '' : ' (scaffold)'}`;
    juzSelect.appendChild(opt);
  });
  juzSelect.value = currentJuz;
}

function populateSelectors() {
  const inJuz = NAV.juz[currentJuz].surahs;
  surahSelect.innerHTML = '';
  inJuz.forEach(num => {
    const s = NAV.surahs[num];
    const opt = document.createElement('option');
    opt.value = num;
    opt.textContent = `${num}. ${s.name}${s.content ? '' : ' ◷'}`;
    surahSelect.appendChild(opt);
  });
  if (!inJuz.includes(currentSurah)) currentSurah = inJuz[0];
  surahSelect.value = currentSurah;

  pageSelect.innerHTML = '';
  pageSelect.appendChild(new Option('All pages', ''));
  const pages = NAV.surahs[currentSurah].pages;
  pages.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p;
    const range = NAV.pages[p] ? ` (${NAV.pages[p].range})` : '';
    opt.textContent = `Page ${p}${range}`;
    pageSelect.appendChild(opt);
  });
  if (currentPage !== null && pages.includes(currentPage)) pageSelect.value = currentPage;
  else pageSelect.value = '';
}

// ─── Load data file ────────────────────────────────────────────────
async function loadSurah(num) {
  const info = NAV.surahs[num];
  if (loadedData[num]) return loadedData[num];
  statusEl.textContent = `Loading ${info.name}…`;
  statusEl.className = 'status loading';
  try {
    const res = await fetch(info.file);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    loadedData[num] = data;
    return data;
  } catch (e) {
    statusEl.textContent = `Failed to load ${info.file}. Serve over HTTP (python3 -m http.server 8000) or verify file exists.`;
    statusEl.className = 'status error';
    throw e;
  }
}

async function loadTajweed(surahNum) {
  if (tajweedCache[surahNum]) return tajweedCache[surahNum];
  try {
    const res = await fetch(`data/tajweed-${surahNum}.json`);
    if (!res.ok) return null;
    const d = await res.json();
    tajweedCache[surahNum] = d;
    return d;
  } catch (e) { return null; }
}

// ─── Tajweed rendering ─────────────────────────────────────────────
// Returns an array of {text, cls} spans for an arabic string given tokens.
function renderArabicWordWithTajweed(wordText, tokens, styleKey) {
  if (!tokens || !tokens.length) return null; // no token layer → caller renders plain
  const clsMap = TAJWEED_STYLES[styleKey].rules;
  return tokens.map(t => {
    const rule = t.r;
    const cls = (rule && clsMap[rule]) ? clsMap[rule] : '';
    return { text: t.c, cls };
  });
}

// ─── Scaffold guard ────────────────────────────────────────────────
function renderScaffoldNotice(surahInfo) {
  verseList.innerHTML = '';
  statusEl.className = 'status';
  statusEl.textContent = '';
  const section = document.createElement('div');
  section.className = 'verse-section';
  const juzList = surahInfo.juz.map(j => `Juz ${j}`).join(', ');
  section.innerHTML = `
    <div class="verse-section-header">
      <div class="verse-section-title">${surahInfo.name} <span>${surahInfo.name_arabic}</span></div>
      <div class="verse-count">${surahInfo.ayahs} ayahs · ${juzList}</div>
    </div>
    <div class="scaffold-notice">
      <div class="scaffold-badge">Scaffold</div>
      <p><strong>${surahInfo.name}</strong> (${surahInfo.name_arabic}) is scaffolded but its verse content has not yet been populated by the ETL pipeline.</p>
      <p class="scaffold-meta">Revelation: ${surahInfo.revelation_type} · Pages ${surahInfo.pages[0]}–${surahInfo.pages[surahInfo.pages.length-1]} · ${surahInfo.ayahs} ayahs · ${juzList}.</p>
      <p class="scaffold-hint">Routing is live for all 30 juz / 114 surahs / 604 pages. Content (verse text, word-by-word translation, morphology, tafsir, and progressive wazn) follows per the architecture's accuracy-over-coverage convention. Juz 1 (Al-Fatihah + Al-Baqarah) is fully populated.</p>
    </div>`;
  verseList.appendChild(section);
}

// ─── Render verses ─────────────────────────────────────────────────
async function renderVerses(data, filterPage) {
  const info = NAV.surahs[currentSurah];
  if (!info.content) { renderScaffoldNotice(info); return; }
  verseList.innerHTML = '';
  statusEl.className = 'status';
  statusEl.textContent = '';

  const tjData = settings.tajweed ? await loadTajweed(currentSurah) : null;

  const ayahs = data.ayahs.filter(a => !filterPage || a.page === filterPage);
  const section = document.createElement('div');
  section.className = 'verse-section';

  const header = document.createElement('div');
  header.className = 'verse-section-header';
  header.innerHTML = `
    <div class="verse-section-title">${data.meta.surah}. ${data.meta.surah_name} <span>${data.meta.surah_name_arabic}</span></div>
    <div class="verse-count">${ayahs.length} ayahs${filterPage ? ` · page ${filterPage}` : ''}</div>
  `;
  section.appendChild(header);

  ayahs.forEach(ayah => {
    const card = document.createElement('div');
    card.className = 'ayah-card';
    card.innerHTML = `
      <div class="ayah-header">
        <span class="ayah-number">${ayah.verse_key}</span>
        <span class="ayah-meta">p.${ayah.page} · j.${ayah.juz}</span>
      </div>
    `;

    const arabicDiv = document.createElement('div');
    arabicDiv.className = 'ayah-arabic';
    const words = (ayah.words && ayah.words.length) ? ayah.words : [{ location: ayah.verse_key + ':0', arabic: ayah.arabic, translation: '' }];
    const tjTokens = tjData && tjData.ayahs ? tjData.ayahs[ayah.verse_key] : null;

    if (tjTokens && settings.tajweed) {
      // token-level colouring
      tjTokens.forEach(tok => {
        const span = document.createElement('span');
        span.className = 'word tj-word' + (tok.r && TAJWEED_STYLES[settings.tajweedStyle].rules[tok.r] ? ' ' + TAJWEED_STYLES[settings.tajweedStyle].rules[tok.r] : '');
        span.textContent = tok.c;
        span.setAttribute('data-location', ayah.verse_key + ':0');
        span.addEventListener('click', () => openStudyPane(words[0], ayah));
        span.addEventListener('mouseenter', () => highlightPair(ayah.verse_key + ':0', true));
        span.addEventListener('mouseleave', () => highlightPair(ayah.verse_key + ':0', false));
        arabicDiv.appendChild(span);
      });
    } else {
      words.forEach(word => {
        const span = document.createElement('span');
        span.className = 'word';
        span.textContent = word.arabic;
        span.setAttribute('data-location', word.location);
        span.addEventListener('click', () => openStudyPane(word, ayah));
        span.addEventListener('mouseenter', () => highlightPair(word.location, true));
        span.addEventListener('mouseleave', () => highlightPair(word.location, false));
        arabicDiv.appendChild(span);
      });
    }
    card.appendChild(arabicDiv);

    const transDiv = document.createElement('div');
    transDiv.className = 'ayah-translation';
    words.forEach(word => {
      if (!word.translation) return;
      const span = document.createElement('span');
      span.className = 'tword';
      span.textContent = word.translation;
      span.setAttribute('data-location', word.location);
      span.addEventListener('mouseenter', () => highlightPair(word.location, true));
      span.addEventListener('mouseleave', () => highlightPair(word.location, false));
      transDiv.appendChild(span);
      transDiv.appendChild(document.createTextNode(' '));
    });
    card.appendChild(transDiv);

    section.appendChild(card);
  });

  verseList.appendChild(section);

  if (settings.tajweed && !tjData) {
    const note = document.createElement('div');
    note.className = 'tajweed-pending';
    note.textContent = 'Tajweed colour coding is on, but token-level annotations for this surah are not yet available. They populate per juz via the ETL pipeline.';
    verseList.appendChild(note);
  }
}

// ─── Bidirectional Highlighting ─────────────────────────────────────
function highlightPair(location, active) {
  const a = document.querySelector(`.word[data-location="${location}"]`);
  const t = document.querySelector(`.tword[data-location="${location}"]`);
  if (a) a.classList.toggle('highlight', active);
  if (t) t.classList.toggle('highlight', active);
}

// ─── Tafsir: merge embedded + registry ─────────────────────────────
function getTafsirList(ayah) {
  const embedded = (ayah.tafsir || []).map(t => ({
    source_id: t.source_id, source_name: t.source_name, author: t.author,
    text: t.text, verification_status: t.verification_status, embedded: true
  }));
  const out = [];
  const seen = new Set();
  if (tafsirRegistry && tafsirRegistry.default_order) {
    tafsirRegistry.default_order.forEach(sid => {
      const reg = tafsirRegistry.editions[sid];
      if (!reg) return;
      const emb = embedded.find(e => e.source_id === sid);
      if (emb) { out.push(emb); seen.add(sid); }
      else {
        // registered but not yet populated for this verse — show as pending
        // so the full mainstream set is always selectable (never fabricated text).
        out.push({ source_id: sid, source_name: reg.name, author: reg.author, text: null, pending: true });
        seen.add(sid);
      }
    });
    // any embedded not in registry order (defensive)
    embedded.forEach(e => { if (!seen.has(e.source_id)) { out.push(e); seen.add(e.source_id); } });
  } else {
    out.push(...embedded);
  }
  return out;
}

function populateTafsirSelector(ayah) {
  tafsirSelect.innerHTML = '';
  const list = getTafsirList(ayah);
  if (!list.length) {
    tafsirSelect.appendChild(new Option('No tafsir available', -1));
    tafsirSelect.disabled = true;
    selectedTafsirIndex = -1;
    return;
  }
  tafsirSelect.disabled = false;
  list.forEach((t, i) => {
    const o = new Option(t.text ? t.source_name : `${t.source_name} (pending)`, i);
    tafsirSelect.appendChild(o);
  });
  window._tafsirList = list;
  if (selectedTafsirIndex >= list.length) selectedTafsirIndex = 0;
  tafsirSelect.value = selectedTafsirIndex;
  tafsirSelect.onchange = () => {
    selectedTafsirIndex = parseInt(tafsirSelect.value);
    if (currentWord && currentAyah) renderStudyContent(currentWord, currentAyah);
  };
}

// ─── Open Study Pane ───────────────────────────────────────────────
function openStudyPane(word, ayah) {
  currentWord = word;
  currentAyah = ayah;
  document.querySelectorAll('.word.selected').forEach(el => el.classList.remove('selected'));
  const wordEl = document.querySelector(`.word[data-location="${word.location}"]`);
  if (wordEl) wordEl.classList.add('selected');

  studyArabic.textContent = word.arabic;
  studyTranslation.textContent = word.translation || '';
  studyLocation.textContent = `${ayah.verse_key} · word ${word.position || word.location.split(':')[2]}`;
  populateTafsirSelector(ayah);
  renderStudyContent(word, ayah);

  studyPane.classList.add('open');
  overlay.classList.add('open');
  isPaneOpen = true;
  studyContent.scrollTop = 0;
}

// ─── Render Study Content ──────────────────────────────────────────
function renderStudyContent(word, ayah) {
  studyContent.innerHTML = '';
  const wz = word.wazn || null;

  if (word.root) {
    const s = document.createElement('div'); s.className = 'study-section';
    s.innerHTML = `<div class="section-label">Root</div><div class="root-card"><div class="root-arabic">${word.root}</div><div class="root-info"><div class="root-letters">${word.root}</div><div class="root-meaning">${word.root_meaning || ''}</div></div></div>`;
    studyContent.appendChild(s);
  } else if (word.morphology && word.morphology.tag) {
    const s = document.createElement('div'); s.className = 'study-section';
    s.innerHTML = `<div class="section-label">Root</div><div class="no-root">${wz && wz.meaning ? wz.meaning : 'This word has no lexical root.'}</div>`;
    studyContent.appendChild(s);
  }

  if (word.morphology) {
    const m = word.morphology;
    const s = document.createElement('div'); s.className = 'study-section';
    s.innerHTML = `<div class="section-label">Morphology</div><div class="morph-tag"><span class="tag-code">${m.tag || ''}</span>${m.description || ''}</div>${m.arabic_grammar ? `<div class="morph-grammar">${m.arabic_grammar}</div>` : ''}`;
    studyContent.appendChild(s);
  }

  if (wz && wz.pattern_arabic) {
    const s = document.createElement('div'); s.className = 'study-section';
    let ex = '';
    if (wz.examples && wz.examples.length) {
      ex = '<div class="wazn-examples">' + wz.examples.map(e => `<span class="wazn-example-chip"><span class="ex-word">${e.word}</span><span class="ex-meaning">${e.meaning}</span></span>`).join('') + '</div>';
    }
    s.innerHTML = `
      <div class="section-label">Pattern</div>
      <div class="wazn-card">
        <div class="wazn-pattern"><span class="wazn-template">${wz.pattern_arabic}</span><span class="wazn-form">${wz.form || ''}</span></div>
        <button class="wazn-toggle" aria-expanded="false">Show pattern details <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>
        <div class="wazn-details">
          <div class="wazn-meaning">${wz.meaning || ''}</div>
          ${wz.root_in_template ? `<div class="wazn-template-visual">${wz.root_in_template}</div>` : ''}
          ${ex}
        </div>
      </div>`;
    studyContent.appendChild(s);
    const tog = s.querySelector('.wazn-toggle'); const det = s.querySelector('.wazn-details');
    tog.addEventListener('click', () => {
      const open = det.classList.contains('expanded');
      det.classList.toggle('expanded'); tog.classList.toggle('expanded');
      tog.innerHTML = open ? `Show pattern details <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>` : `Hide details <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;
      tog.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  }

  // Tafsir (multi-edition)
  const list = window._tafsirList || getTafsirList(ayah);
  const s = document.createElement('div'); s.className = 'study-section';
  s.innerHTML = `<div class="section-label">Tafsir</div>`;
  const t = list[selectedTafsirIndex] || list[0];
  if (t && t.text) {
    const isLong = t.text.length > 250;
    s.innerHTML += `<div class="tafsir-card"><div class="tafsir-source">${t.source_name}${t.author ? ` · ${t.author}` : ''}</div><div class="tafsir-text${isLong ? ' collapsed' : ''}" id="tafsirText">${t.text}</div>${isLong ? `<button class="tafsir-expand" id="tafsirExpand" aria-expanded="false">Read more <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></button>` : ''}</div>`;
    studyContent.appendChild(s);
    if (isLong) {
      const eb = document.getElementById('tafsirExpand'); const tt = document.getElementById('tafsirText');
      eb.addEventListener('click', () => {
        const open = tt.classList.contains('collapsed');
        tt.classList.toggle('collapsed'); eb.classList.toggle('expanded');
        eb.innerHTML = open ? `Show less <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>` : `Read more <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`;
        eb.setAttribute('aria-expanded', open ? 'false' : 'true');
      });
    }
  } else if (t && t.pending) {
    s.innerHTML += `<div class="no-tafsir">${t.source_name} is registered but its content for this verse has not been populated yet (ETL pending).</div>`;
    studyContent.appendChild(s);
  } else {
    s.innerHTML += `<div class="no-tafsir">No tafsir available for this verse yet.</div>`;
    studyContent.appendChild(s);
  }

  // Qira'at (variant readings) — separate dimension from typeface/script.
  // Lazy hook to quran.com's QDC matrix; honest fallback if region-gated.
  const qsection = document.createElement('div'); qsection.className = 'study-section';
  qsection.innerHTML = `<div class="section-label">Qira'at (variant readings)</div><div class="no-tafsir" id="qiraatNote">Loading variant readings…</div>`;
  studyContent.appendChild(qsection);
  loadQiraat(ayah.verse_key).then(junctures => {
    const note = qsection.querySelector('#qiraatNote');
    if (!junctures || !junctures.length) { note.textContent = 'Variant readings matrix is not reachable from this network yet (quran.com QDC endpoint region-gated). The base text is Hafs an-Asim. This is a documented fetch hook for ETL.'; return; }
    let html = '';
    junctures.forEach(j => {
      (j.readings || []).forEach(rd => {
        const color = QIRAAT_CARD_COLORS[(rd.color||'').toLowerCase()] || QIRAAT_CARD_COLORS.blue;
        html += `<div style="display:flex;gap:10px;align-items:baseline;padding:6px 0;border-bottom:1px solid var(--border);"><span style="min-width:54px;height:10px;border-radius:2px;background:${color};display:inline-block;"></span><span class="occ-form" style="font-family:var(--font-arabic);font-size:16px;color:var(--ink);direction:rtl;">${rd.textUthmani || rd.text || ''}</span><span style="font-size:12px;color:var(--ink-muted);">${rd.translation || ''}</span></div>`;
      });
    });
    note.outerHTML = html || '<div class="no-tafsir">No variant readings recorded for this juncture.</div>';
  });

  // Themes (contemporary connection layer — Level 3 / Explore).
  // Curated tags linking classical tafsir to contemporary ethical/philosophical
  // inquiry. Loaded once from data/themes.json, keyed by verse_key. Renders
  // theme chips with a one-line description; honest empty state when data is absent.
  const thSection = document.createElement('div'); thSection.className = 'study-section';
  thSection.innerHTML = `<div class="section-label">Themes &amp; relevance</div><div class="no-tafsir" id="themesNote">Loading themes…</div>`;
  studyContent.appendChild(thSection);
  loadThemes().then(themeData => {
    const note = thSection.querySelector('#themesNote');
    const themes = (themeData && themeData.themes) ? themeData.themes : [];
    const forVerse = themes.filter(t => t.verse_key === ayah.verse_key);
    if (!forVerse.length) {
      note.textContent = 'No curated themes for this verse yet — the contemporary-relevance layer populates as content is added.';
      return;
    }
    let chips = '';
    forVerse.forEach(t => {
      chips += `<span class="wazn-example-chip" style="display:inline-flex;align-items:flex-start;gap:6px;padding:6px 12px;border-radius:14px;background:var(--accent-light);border:none;max-width:100%;"><span style="font-weight:600;color:var(--accent-ink);white-space:nowrap;">${t.theme}</span><span style="color:var(--ink-muted);font-size:12.5px;line-height:1.5;">${t.description || ''}</span></span>`;
    });
    note.outerHTML = `<div style="display:flex;flex-wrap:wrap;gap:8px;">${chips}</div>`;
  });
}

// ─── Close Study Pane ───────────────────────────────────────────────
function closeStudyPane() {
  studyPane.classList.remove('open'); overlay.classList.remove('open'); isPaneOpen = false;
  document.querySelectorAll('.word.selected, .highlight').forEach(el => el.classList.remove('selected', 'highlight'));
}
overlay.addEventListener('click', closeStudyPane);
let startY = 0;
paneHandle.addEventListener('touchstart', e => { startY = e.touches[0].clientY; }, { passive: true });
paneHandle.addEventListener('touchend', e => { if (e.changedTouches[0].clientY - startY > 60) closeStudyPane(); }, { passive: true });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && isPaneOpen) closeStudyPane(); });

// ─── Navigation handlers ───────────────────────────────────────────
juzSelect.addEventListener('change', async () => {
  currentJuz = parseInt(juzSelect.value); currentSurah = NAV.juz[currentJuz].surahs[0]; currentPage = null;
  populateSelectors();
  try { renderVerses(await loadSurah(currentSurah), null); } catch (e) {}
});
surahSelect.addEventListener('change', async () => {
  currentSurah = parseInt(surahSelect.value); currentPage = null; populateSelectors();
  try { renderVerses(await loadSurah(currentSurah), null); } catch (e) {}
});
pageSelect.addEventListener('change', async () => {
  currentPage = pageSelect.value ? parseInt(pageSelect.value) : null;
  try { renderVerses(await loadSurah(currentSurah), currentPage); } catch (e) {}
});

// ─── Settings handlers ─────────────────────────────────────────────
tajweedToggle.addEventListener('change', () => {
  settings.tajweed = tajweedToggle.checked;
  tajweedStyleSel.disabled = !settings.tajweed;
  saveSettings();
  try { renderVerses(loadedData[currentSurah], currentPage); } catch (e) {}
});
tajweedStyleSel.addEventListener('change', () => {
  settings.tajweedStyle = tajweedStyleSel.value;
  saveSettings();
  try { renderVerses(loadedData[currentSurah], currentPage); } catch (e) {}
});
scriptSel.addEventListener('change', () => { settings.script = scriptSel.value; applyTheme(); });
themeSel.addEventListener('change', () => { settings.theme = themeSel.value; applyTheme(); });
inkSel.addEventListener('change', () => { settings.ink = inkSel.value; applyTheme(); });

// ─── Init ──────────────────────────────────────────────────────────
(async () => {
  loadSettings();
  if (location.protocol === 'file:') {
    statusEl.className = 'status help';
    statusEl.textContent = 'Opening via file:// — data files are blocked by the browser. Run: python3 -m http.server 8000 and open http://localhost:8000/';
  }
  try {
    const res = await fetch('navigation.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    NAV = await res.json();
    // tafsir registry
    try {
      const r2 = await fetch('data/tafsir-registry.json');
      tafsirRegistry = r2.ok ? await r2.json() : null;
    } catch (e) { tafsirRegistry = null; }
    applyTheme();
    populateSettingsControls();
    populateJuzSelect();
    populateSelectors();
    renderVerses(await loadSurah(currentSurah), null);
  } catch (e) {
    statusEl.className = 'status error';
    statusEl.textContent = 'Failed to load navigation.json. Serve over HTTP (python3 -m http.server 8000).';
  }
})();
