/**
 * Shared helpers of the learning pages and the search results.
 *
 * Two things are done here, and neither makes a form:
 *   - a phonetic form, as Parks prints it, is cut at its syllable dots and each
 *     symbol is given a plain-English hint (the hints are the project's, the same
 *     as on the Sounds page);
 *   - a derivation, as Parks prints it, is shown piece by piece (the pieces were
 *     cut at his plus signs by web/learning.py).
 */
const Skiri = (() => {
  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  // ---------------------------------------------------------------- sounds
  // Hints for the symbols of Parks's phonetic forms. English has no exact match for most of them.
  const SOUNDS = {
    'p': ['p', 'as in <b>sp</b>in: no puff of air'],
    't': ['t', 'as in <b>st</b>op: no puff of air'],
    'k': ['k', 'as in <b>sk</b>in: no puff of air'],
    'ts': ['ts', 'as in ca<b>ts</b> (the letter <i>c</i> before a consonant or at the end of a word)'],
    'č': ['č', 'as in <b>ch</b>in (the letter <i>c</i> before a vowel)'],
    's': ['s', 'as in <b>s</b>it'],
    'h': ['h', 'as in <b>h</b>it; breathier before a consonant'],
    'w': ['w', 'as in <b>w</b>all'],
    'r': ['r', 'a quick tap, like the middle of <i>bu<b>tt</b>er</i> said fast; at the start of a word many speakers said <i>n</i>'],
    'n': ['n', 'as in <b>n</b>o'],
    'ʔ': ['ʔ', 'the catch in the middle of <i>uh-oh</i> (glottal stop)'],
    'a': ['a', 'short, as in f<b>a</b>ther but brief'],
    'ə': ['ə', 'short, as in <b>a</b>bove or p<b>u</b>tt'],
    'i': ['i', 'short, as in mach<b>i</b>ne but brief'],
    'ɪ': ['ɪ', 'short, as in p<b>i</b>t'],
    'u': ['u', 'short, as in r<b>u</b>de but brief'],
    'ʊ': ['ʊ', 'short, as in p<b>u</b>t'],
    'aa': ['aa', 'long, as in f<b>a</b>ther, held about twice as long'],
    'ii': ['ii', 'long, as in w<b>ee</b>d, held about twice as long'],
    'uu': ['uu', 'long, as in r<b>u</b>de, held about twice as long'],
    '{k/t}': ['k/t', 'Parks prints both: the stem ends in <i>k</i> in some forms and in <i>t</i> in others'],
    'Ø': ['Ø', 'a stem with no sound of its own; the word is made of what is added to it'],
  };
  const ACUTE = '́', GRAVE = '̀', CARON = '̌';

  // One syllable (in NFD) -> tokens {show, key, accent}
  function tokens(syllable) {
    const out = [];
    let i = 0;
    const s = syllable;
    while (i < s.length) {
      const rest = s.slice(i);
      let m;
      if ((m = rest.match(/^\{[^}]*\}/))) {
        out.push({ show: m[0].slice(1, -1), key: m[0] });
      } else if ((m = rest.match(new RegExp('^([aiu])([' + ACUTE + GRAVE + ']?)\\1([' + ACUTE + GRAVE + ']?)')))) {
        out.push({ show: m[0], key: m[1] + m[1], accent: (m[2] || m[3]) === ACUTE, grave: (m[2] || m[3]) === GRAVE });
      } else if ((m = rest.match(new RegExp('^([aəiɪuʊ])([' + ACUTE + GRAVE + ']?)')))) {
        out.push({ show: m[0], key: m[1], accent: m[2] === ACUTE, grave: m[2] === GRAVE });
      } else if (rest.startsWith('c' + CARON)) {
        m = ['c' + CARON];
        out.push({ show: 'č', key: 'č' });
      } else if (rest.startsWith('ts')) {
        m = ['ts'];
        out.push({ show: 'ts', key: 'ts' });
      } else {
        m = [rest[0]];
        out.push({ show: rest[0], key: rest[0] });
      }
      i += m[0].length;
    }
    return out;
  }

  /**
   * A printed phonetic form -> its variants, words and syllables.
   * "[kaá·ʔə·sə·sʊʔ, kaá·sə·sʊʔ]" has two variants; "[–ət– ɪs·tʊʔ]" two words.
   */
  function parsePhonetic(phonetic) {
    let s = String(phonetic || '').trim().normalize('NFD');
    if (s.startsWith('[')) s = s.slice(1);
    if (s.endsWith(']')) s = s.slice(0, -1);
    s = s.replace(/\s*\([^)]*\.\.\.\)/g, '');           // a preverb note such as (ʊt...) is not part of the word
    return s.split(/\s*,\s*/).filter(Boolean).map(variant =>
      variant.split(/\s+/).filter(Boolean).map(word =>
        word.split('·').filter(Boolean).map(syl => {
          const toks = tokens(syl);
          return { text: syl.normalize('NFC'), tokens: toks, accented: toks.some(t => t.accent) };
        })));
  }

  /** The syllable tiles and the list of sounds for one printed phonetic form. `say` is the rough respelling. */
  function soundItOut(phonetic, say) {
    const variants = parsePhonetic(phonetic);
    if (!variants.length) return '';
    const sayVariants = String(say || '').split(/\s*\/\s*/);
    const seen = new Map();
    let bound = false, optional = false, alternates = false, grave = false;
    const rows = variants.map((words, vi) => {
      const flat = words.reduce((a, w) => a.concat(w), []);
      // the respelling has one chunk to a syllable when it was made from this form; show it only then
      const chunks = (sayVariants[vi] || '').replace(/\s+/g, '-').split('-').filter(Boolean);
      const aligned = chunks.length === flat.length;
      let n = 0;
      const wordHtml = words.map(word => '<span class="syl-word">' + word.map(syl => {
        const chunk = aligned ? chunks[n] : '';
        n += 1;
        for (const t of syl.tokens) {
          if (t.key === '–') bound = true;
          else if (t.key === '(' || t.key === ')') optional = true;
          else if (t.key === '/') alternates = true;
          else if (SOUNDS[t.key] && !seen.has(t.key)) seen.set(t.key, SOUNDS[t.key]);
          if (t.grave) grave = true;
        }
        return `<span class="syl${syl.accented ? ' syl--accent' : ''}"><span class="syl-ipa" lang="x-paw">${esc(syl.text)}</span>` +
          `${chunk ? `<span class="syl-say">${esc(chunk)}</span>` : ''}</span>`;
      }).join('') + '</span>').join('');
      return `<div class="syl-row">${wordHtml}</div>`;
    }).join('');

    const notes = [];
    if (variants.some(v => v.some(w => w.some(s => s.accented)))) {
      notes.push('The darker syllable is the accented one: Parks marks it with an accent in his phonetic form.');
    } else {
      notes.push('Parks marks no accent in the phonetic form of this word.');
    }
    if (bound) notes.push('A dash at the edge (–) means this is a stem, not a whole word: something is always added on that side.');
    if (optional) notes.push('A sound in parentheses is printed that way by Parks: it is not there in every form of the word.');
    if (alternates) notes.push('A slash separates two shapes Parks gives for the same stem.');
    if (grave) notes.push('Parks prints a second accent mark (the one leaning left) on this word. His dictionary does not say what it marks.');

    const list = Array.from(seen.values()).map(([sym, hint]) =>
      `<li><span class="sound-sym" lang="x-paw">${esc(sym)}</span> ${hint}</li>`).join('');
    return `<div class="sound-out">${rows}<ul class="sound-list">${list}</ul>` +
      `<p class="sound-notes">${notes.join(' ')}</p></div>`;
  }

  // ---------------------------------------------------------------- pieces
  /** The pieces of a printed derivation as a row of chips. `build` is {u, k, lit, words?, unsure?}. */
  function pieceChips(build, options) {
    const opts = options || {};
    const link = opts.link === undefined ? 'words.html?piece=' : opts.link;
    const words = build.words || [];
    return '<span class="piece-row">' + build.u.map((unit, i) => {
      const gap = i > 0 && words.length && words[i] !== words[i - 1];
      const cls = 'piece' + (opts.highlight && build.k[i] === opts.highlight ? ' piece--on' : '');
      const chip = link
        ? `<a class="${cls}" lang="x-paw" href="${esc(link + encodeURIComponent(build.k[i]))}" title="Other words with this piece">${esc(unit)}</a>`
        : `<span class="${cls}" lang="x-paw">${esc(unit)}</span>`;
      return (i > 0 ? `<span class="piece-plus${gap ? ' piece-plus--word' : ''}">${gap ? '' : '+'}</span>` : '') + chip;
    }).join('') + '</span>';
  }

  /** Parks's literal translation, with his capital-letter labels explained on hover. `labels`: {NOM: {meaning}}. */
  function literalHtml(literal, labels) {
    if (!literal) return '';
    const known = labels || BASIC_LABELS;
    return esc(literal).replace(/\b[A-Z][A-Z0-9]+(?:[.\/][A-Z0-9]+)*\b/g, token => {
      const entry = known[token] || null;
      const parts = entry ? [entry] : token.split(/[.\/]/).map(t => known[t]).filter(Boolean);
      if (!parts.length) return token;
      const title = parts.map(p => p.meaning || p).join('; ');
      return `<abbr class="gram-label" title="${esc(title)}">${token}</abbr>`;
    });
  }

  // The labels most often printed in a literal translation, for pages that do not load the full list.
  const BASIC_LABELS = {
    NOM: { meaning: 'nominal/absolutive suffix: marks a noun standing on its own' },
    DIM: { meaning: 'diminutive suffix' }, AUG: { meaning: 'augmentative suffix' },
    LOC: { meaning: 'locative' }, PL: { meaning: 'plural' }, DIST: { meaning: 'distributive' },
    ITER: { meaning: 'iterative' }, PERF: { meaning: 'perfective' }, IMPF: { meaning: 'imperfective' },
    PORT: { meaning: 'portative' }, PREV: { meaning: 'preverb' }, CAUS: { meaning: 'causative' },
    INCH: { meaning: 'inchoative' }, FEM: { meaning: 'feminine' },
  };

  /** The block shown under a search result: the pieces, Parks's literal translation, and where to go on. */
  function buildBlock(build) {
    if (!build || !build.u || build.u.length < 2) return '';
    return `<div class="build-block">${pieceChips(build)}` +
      `${build.lit ? `<p class="build-literal">Parks's literal translation: <span class="build-lit-text">${literalHtml(build.lit)}</span></p>` : ''}` +
      `${build.unsure ? '<p class="result-usage">Parks marks this analysis as uncertain.</p>' : ''}` +
      '<p class="result-usage">Each piece is as the dictionary prints it. Choose one to see the other words that have it.</p></div>';
  }

  // ---------------------------------------------------------------- small things
  function entryLink(id) {
    return 'index.html?id=' + encodeURIComponent(id);
  }

  function shuffle(list) {
    const a = list.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // localStorage that never throws (private windows, blocked storage)
  const store = {
    get(key, fallback) {
      try {
        const raw = window.localStorage.getItem(key);
        return raw == null ? fallback : JSON.parse(raw);
      } catch (e) { return fallback; }
    },
    set(key, value) {
      try { window.localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* not kept */ }
    },
  };

  async function load(name) {
    const response = await fetch('data/' + name + '.json');
    if (!response.ok) throw new Error(name + ': ' + response.status);
    return response.json();
  }

  return { esc, SOUNDS, parsePhonetic, soundItOut, pieceChips, literalHtml, buildBlock, entryLink, shuffle, store, load };
})();
