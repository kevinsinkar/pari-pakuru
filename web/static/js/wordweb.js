/**
 * The word web: words as boxes, joined to the pieces printed in their derivations.
 * Data: data/wordbuilding.json (web/learning.py, wordbuilding_data), the file the word-building page reads.
 *
 * Nothing here makes a form or an analysis.
 *   - A box is a dictionary entry: its headword and its first meaning, as printed.
 *   - An oval is a piece of a printed derivation, cut at Parks's plus signs (web/learning.py does the cutting).
 *   - A line joins a word to a piece that the dictionary prints in that word's derivation.
 * Words hang on one oval when the dictionary prints the same letters for the piece, and that is all an oval says:
 * the same letters are not always the same piece, and the page does not say what a piece means.
 * Where the boxes and ovals are put on the page is worked out here; it carries no meaning.
 *
 * The first half of this file (the model and the layout) needs no page and is run by scripts/check_static_site.js.
 */
const WordWeb = (() => {
  'use strict';

  const SETTINGS = {
    step: 10,         // words that a click on an oval brings in
    startWords: 12,   // words drawn at once round the piece a picture starts from
    queryWords: 24,   // words drawn at once for an English word
    relatives: 5,     // other words drawn for each piece of the word a picture starts from
    common: 60,       // a piece printed in more words than this is not opened without being asked
    maxWords: 150,    // the picture stops growing here
  };

  // ------------------------------------------------------------------ what is looked up
  /** A piece as the data keys it: plain letters, no accent, hyphen or parenthesis (the same rule as words.js). */
  function plainKey(text) {
    return String(text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
      .replace(/[\s\-()]/g, '').replace(/ø/g, 'Ø');
  }

  /** An English word as a whole word, with its plain plural: "bear" finds "bear" and "bears", not "beard". */
  function englishPattern(text) {
    const q = String(text || '').toLowerCase().trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return q ? new RegExp('\\b' + q + '(?:s|es)?\\b') : null;
  }

  function makeIndex(data) {
    const byKey = new Map();    // piece -> indexes of the entries whose printed derivation has it
    const byId = new Map();     // entry id -> index
    data.entries.forEach((entry, i) => {
      byId.set(entry.id, i);
      new Set(entry.k).forEach(key => {
        if (!byKey.has(key)) byKey.set(key, []);
        byKey.get(key).push(i);
      });
    });
    return { byKey, byId };
  }

  /** What stands in a box. A long headword or meaning is cut, with a mark that it was; the panel shows it whole. */
  function wordLabel(entry) {
    const w = String(entry.w || '');
    return w.length > 26 ? w.slice(0, 25).replace(/[\s,]+$/, '') + '…' : w;
  }

  function glossLabel(entry) {
    let g = String(entry.g || '').split(' (')[0].replace(/[.;,:\s]+$/, '');
    if (g.length > 30) {
      g = g.slice(0, 30);
      const cut = g.lastIndexOf(' ');
      g = (cut > 14 ? g.slice(0, cut) : g).replace(/[.;,:\s]+$/, '') + '…';
    }
    return g;
  }

  // ------------------------------------------------------------------ the picture: which words and pieces, joined how
  function createPicture(data, index) {
    const entries = data.entries;
    const nodes = [], links = [];
    const words = new Map();     // entry index -> node
    const pieces = new Map();    // piece key -> node
    let seed = 1;

    // The same start always gives the same picture: the small offsets come from the start's own name.
    function reseed(text) {
      seed = 2166136261;
      for (const ch of String(text)) { seed ^= ch.codePointAt(0); seed = Math.imul(seed, 16777619); }
    }
    function random() {
      seed = (seed + 0x6D2B79F5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    }

    const total = key => (index.byKey.get(key) || []).length;          // words the dictionary prints the piece in
    const hidden = key => total(key) - (pieces.has(key) ? pieces.get(key).deg : 0);

    function addPiece(key, x, y) {
      let node = pieces.get(key);
      if (!node) {
        node = { id: 'p:' + key, kind: 'piece', key, total: total(key), deg: 0, x, y, vx: 0, vy: 0, hw: 30, hh: 16 };
        pieces.set(key, node);
        nodes.push(node);
      }
      return node;
    }

    /** A word comes with every piece of its printed derivation; none is left out. `from` is the oval it hangs on. */
    function addWord(i, x, y, from) {
      if (words.has(i)) return null;
      if (words.size >= SETTINGS.maxWords) return null;
      const entry = entries[i];
      const node = { id: 'w:' + entry.id, kind: 'word', i, entry, deg: 0, x, y, vx: 0, vy: 0, hw: 60, hh: 21 };
      words.set(i, node);
      nodes.push(node);
      let ux = from ? x - from.x : 0, uy = from ? y - from.y : 0;
      const length = Math.hypot(ux, uy) || 1;
      ux /= length; uy /= length;
      Array.from(new Set(entry.k)).forEach(key => {
        const turn = (random() - 0.5) * 1.6;
        const dx = from ? ux * Math.cos(turn) - uy * Math.sin(turn) : Math.cos(turn * 4);
        const dy = from ? ux * Math.sin(turn) + uy * Math.cos(turn) : Math.sin(turn * 4);
        const piece = addPiece(key, x + dx * 130, y + dy * 80);
        links.push({ word: node, piece });
        node.deg += 1;
        piece.deg += 1;
      });
      return node;
    }

    /** The words of a piece: the shortest derivations first, then the dictionary's order. */
    function wordsOf(key) {
      return (index.byKey.get(key) || []).slice().sort((a, b) => entries[a].k.length - entries[b].k.length || a - b);
    }

    /** Bring in more of the words in which the piece is printed. Returns how many came. */
    function expand(key, limit) {
      const hub = pieces.get(key);
      if (!hub) return 0;
      const waiting = wordsOf(key).filter(i => !words.has(i)).slice(0, limit == null ? SETTINGS.step : limit);
      const base = hub.deg;
      let added = 0;
      waiting.forEach((i, n) => {
        const angle = (base + n) * 2.399963 + random() * 0.4;          // the golden angle spreads them round the oval
        const r = 120 + 12 * Math.sqrt(base + n) + 20 * random();
        if (addWord(i, hub.x + Math.cos(angle) * r * 1.5, hub.y + Math.sin(angle) * r, hub)) added += 1;
      });
      return added;
    }

    function clear(name) {
      nodes.length = 0;
      links.length = 0;
      words.clear();
      pieces.clear();
      reseed(name);
    }

    function startPiece(key) {
      if (!index.byKey.has(key)) return null;
      clear('piece ' + key);
      addPiece(key, 0, 0);
      expand(key, SETTINGS.startWords);
      return { kind: 'piece', key, total: total(key) };
    }

    function startWord(i) {
      if (!entries[i]) return null;
      clear('word ' + entries[i].id);
      addWord(i, 0, 0, null);
      Array.from(new Set(entries[i].k)).forEach(key => {
        if (total(key) <= SETTINGS.common) expand(key, SETTINGS.relatives);
      });
      return { kind: 'word', i };
    }

    /** The words with an English word in the meaning or in the literal translation the dictionary prints. */
    function startEnglish(text) {
      const pattern = englishPattern(text);
      if (!pattern) return null;
      const found = [];
      entries.forEach((e, i) => {
        if (pattern.test(String(e.g || '').toLowerCase()) || pattern.test(String(e.lit || '').toLowerCase())) found.push(i);
      });
      if (!found.length) return null;
      clear('english ' + String(text).toLowerCase().trim());
      const inSet = new Map();
      found.forEach(i => new Set(entries[i].k).forEach(k => inSet.set(k, (inSet.get(k) || 0) + 1)));
      // A piece counts for more when most of the words it is printed in are among those found.
      const weight = k => inSet.get(k) * inSet.get(k) / total(k);
      const score = i => Math.max(...entries[i].k.map(weight));
      const order = found.slice().sort((a, b) => score(b) - score(a) || entries[a].k.length - entries[b].k.length || a - b);
      let best = null;
      inSet.forEach((n, k) => { if (n > 1 && (best === null || weight(k) > weight(best))) best = k; });
      const state = { kind: 'english', text: String(text).trim(), found: order, drawn: 0, best, bestCount: best ? inSet.get(best) : 0 };
      more(state);
      return state;
    }

    /** The next words of an English search, on a widening spiral; then each shared piece goes among its words. */
    function more(state) {
      let added = 0;
      while (state.drawn < state.found.length && added < SETTINGS.queryWords) {
        const n = state.drawn;
        const angle = n * 2.399963, r = 70 + 52 * Math.sqrt(n);
        if (!words.has(state.found[n]) && !addWord(state.found[n], Math.cos(angle) * r * 1.5, Math.sin(angle) * r, null)) break;
        state.drawn += 1;
        added += 1;
      }
      pieces.forEach(piece => {
        if (piece.deg < 2) return;
        let x = 0, y = 0;
        links.forEach(l => { if (l.piece === piece) { x += l.word.x; y += l.word.y; } });
        piece.x = x / piece.deg;
        piece.y = y / piece.deg;
      });
      return added;
    }

    return { nodes, links, words, pieces, total, hidden, wordsOf, expand, startPiece, startWord, startEnglish, more };
  }

  // ------------------------------------------------------------------ sizes and places
  /** The width of a text without a browser, by its count of letters. The page measures the real text instead. */
  function estimate(text, kind) {
    return String(text).length * (kind === 'gloss' || kind === 'count' ? 5.6 : 7.4);
  }

  /** The half width and half height of every shape. A box fits its two lines of text. An oval fits its text and
      grows with the number of its words that are in the picture, so the piece most words share is the largest. */
  function sizes(pic, measure) {
    const m = measure || estimate;
    pic.nodes.forEach(node => {
      if (node.kind === 'word') {
        if (node.label !== undefined) return;
        node.label = wordLabel(node.entry);
        node.gloss = glossLabel(node.entry);
        const w = Math.max(m(node.label, 'word'), node.gloss ? m(node.gloss, 'gloss') : 0);
        node.hw = Math.max(34, w / 2 + 12);
        node.hh = node.gloss ? 21 : 14;
        return;
      }
      if (node.label === undefined) {
        node.label = node.key;
        node.countLabel = node.total > 1 ? node.total + ' words' : '';
        node.textWidth = Math.max(m(node.label, 'piece'), node.countLabel ? m(node.countLabel, 'count') : 0);
      }
      const hh = node.total > 1 ? Math.min(46, 15 + 6 * Math.log2(1 + node.deg)) : 14;
      const hw = Math.max(hh, node.textWidth / 2 * 1.15 + 10);
      if (hh !== node.hh || hw !== node.hw) {
        node.hh = hh;
        node.hw = hw;
        node.resized = true;
      }
    });
  }

  const PAD = 10;

  /** Move apart every two shapes that lie on one another, along the side on which they overlap least.
      Returns how many pairs it found. */
  function collide(pic, strength) {
    const nodes = pic.nodes, n = nodes.length;
    let found = 0;
    for (let a = 0; a < n; a++) {
      const A = nodes[a];
      for (let b = a + 1; b < n; b++) {
        const B = nodes[b];
        const dx = B.x - A.x, dy = B.y - A.y;
        const ox = A.hw + B.hw + PAD - Math.abs(dx), oy = A.hh + B.hh + PAD - Math.abs(dy);
        if (ox <= 0 || oy <= 0) continue;
        found += 1;
        const freeA = A.fixed ? 0 : 1, freeB = B.fixed ? 0 : 1, both = freeA + freeB;
        if (!both) continue;
        if (ox < oy) {
          const s = ox * strength * (dx < 0 || (dx === 0 && a % 2) ? -1 : 1);
          A.x -= s * freeA / both; B.x += s * freeB / both;
        } else {
          const s = oy * strength * (dy < 0 || (dy === 0 && a % 2) ? -1 : 1);
          A.y -= s * freeA / both; B.y += s * freeB / both;
        }
      }
    }
    return found;
  }

  /** One step of the layout: everything pushes everything else away a little, a line pulls its two ends
      together, the whole is held near the middle, and shapes that overlap are moved apart.
      `pic.aspect` is the width of the place for the picture over its height: on a wide screen the picture is
      held more firmly up and down and spreads sideways, on a phone the other way round. */
  function step(pic, alpha) {
    const nodes = pic.nodes, n = nodes.length;
    const wide = Math.max(0, Math.min(1, ((pic.aspect || 1.6) - 0.6) / 0.9));        // 0 on a phone, 1 on a wide screen
    const sideways = 1.5 - 0.9 * wide;
    const holdX = 0.03 - 0.022 * wide, holdY = 0.006 + 0.028 * wide;
    for (let a = 0; a < n; a++) {
      const A = nodes[a];
      for (let b = a + 1; b < n; b++) {
        const B = nodes[b];
        let dx = B.x - A.x, dy = B.y - A.y;
        if (dx === 0 && dy === 0) { dx = (a + b) % 2 ? 0.5 : -0.5; dy = 0.5; }
        const ex = dx * sideways;                              // on a wide screen sideways distance counts for less
        const d2 = Math.max(ex * ex + dy * dy, 900);
        const d = Math.sqrt(d2);
        const f = 4200 * alpha / d2;
        const fx = f * ex / d, fy = f * dy / d;
        A.vx -= fx; A.vy -= fy; B.vx += fx; B.vy += fy;
      }
    }
    pic.links.forEach(link => {
      const A = link.word, B = link.piece;
      const dx = B.x - A.x, dy = B.y - A.y;
      const d = Math.hypot(dx, dy) || 1;
      const rest = 58 + 0.5 * (A.hw + B.hw) + 2 * Math.min(B.deg, 24);
      const pull = (d - rest) / d * 0.12 * alpha;
      const massA = 1 + A.deg, massB = 1 + B.deg;
      const shareA = massB / (massA + massB), shareB = massA / (massA + massB);
      A.vx += dx * pull * shareA; A.vy += dy * pull * shareA;
      B.vx -= dx * pull * shareB; B.vy -= dy * pull * shareB;
    });
    nodes.forEach(node => {
      if (node.fixed) { node.vx = 0; node.vy = 0; return; }
      node.vx = (node.vx - node.x * holdX * alpha) * 0.78;
      node.vy = (node.vy - node.y * holdY * alpha) * 0.78;
      node.x += node.vx;
      node.y += node.vy;
    });
    collide(pic, 0.5);
    collide(pic, 0.5);
  }

  /** Let nothing lie on anything else: the last word of every layout. */
  function tidy(pic) {
    for (let n = 0; n < 120 && collide(pic, 1); n++) { /* until no pair is found */ }
  }

  function settle(pic, ticks, from) {
    let alpha = from || 1;
    for (let t = 0; t < ticks; t++) {
      step(pic, alpha);
      alpha = Math.max(0.04, alpha * 0.988);
    }
    tidy(pic);
  }

  /** How many pairs of shapes still lie on one another (the check wants none). */
  function overlaps(pic) {
    let count = 0;
    for (let a = 0; a < pic.nodes.length; a++) {
      for (let b = a + 1; b < pic.nodes.length; b++) {
        const A = pic.nodes[a], B = pic.nodes[b];
        if (Math.abs(B.x - A.x) < A.hw + B.hw && Math.abs(B.y - A.y) < A.hh + B.hh) count += 1;
      }
    }
    return count;
  }

  function bounds(nodes) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    nodes.forEach(n => {
      x0 = Math.min(x0, n.x - n.hw); x1 = Math.max(x1, n.x + n.hw);
      y0 = Math.min(y0, n.y - n.hh); y1 = Math.max(y1, n.y + n.hh);
    });
    return nodes.length ? { x: x0, y: y0, w: x1 - x0, h: y1 - y0 } : { x: 0, y: 0, w: 1, h: 1 };
  }

  // ------------------------------------------------------------------ the page
  const NS = 'http://www.w3.org/2000/svg';
  const MIN_FIT = 0.55, MAX_FIT = 1.5, MAX_ZOOM = 2.6, MIN_ZOOM = 0.2;

  function svgEl(name, attrs, text) {
    const node = document.createElementNS(NS, name);
    Object.keys(attrs || {}).forEach(k => node.setAttribute(k, attrs[k]));
    if (text != null) node.textContent = text;
    return node;
  }

  async function mount() {
    const { esc, pieceChips, literalHtml, entryLink, load } = Skiri;
    const svg = document.getElementById('ww-svg');
    const panel = document.getElementById('ww-panel');
    const summary = document.getElementById('ww-summary');
    const input = document.getElementById('ww-q');
    let data;
    try {
      data = await load('wordbuilding');
    } catch (error) {
      summary.textContent = 'The word-building data could not be loaded.';
      return;
    }
    if (document.fonts && document.fonts.ready) {      // the boxes are sized by the real width of their text
      await Promise.race([document.fonts.ready, new Promise(done => setTimeout(done, 1500))]);
    }
    const index = makeIndex(data);
    const pic = createPicture(data, index);
    const world = svgEl('g', { class: 'ww-world' });
    const linkLayer = svgEl('g', { class: 'ww-links' });
    const nodeLayer = svgEl('g', { class: 'ww-nodes' });
    world.appendChild(linkLayer);
    world.appendChild(nodeLayer);
    svg.appendChild(world);

    const still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const view = { k: 1, x: 0, y: 0 };
    let state = null;          // what the picture was started from
    let selected = null;
    let autoFit = true;        // the picture keeps itself in view until the visitor moves it
    let alpha = 0, frame = 0;

    // ---- measuring text
    const ruler = document.createElement('canvas').getContext('2d');
    const FONTS = {
      word: '500 14px "Source Serif 4", "Gentium Plus", "Charis SIL", serif',
      piece: '500 14px "Source Serif 4", "Gentium Plus", "Charis SIL", serif',
      gloss: '10.5px "DM Sans", system-ui, sans-serif',
      count: '10.5px "DM Sans", system-ui, sans-serif',
    };
    function measure(text, kind) {
      if (!ruler) return estimate(text, kind);
      ruler.font = FONTS[kind];
      return ruler.measureText(text).width;
    }

    // ---- drawing
    function describe(node) {
      if (node.kind === 'word') {
        return node.entry.w + ': ' + (node.entry.g || '') + ' Pieces printed in its derivation: ' + node.entry.u.join(' + ');
      }
      const waiting = pic.hidden(node.key);
      return 'The piece ' + node.key + ', printed in ' + node.total + (node.total === 1 ? ' word' : ' words') +
        (waiting ? '; ' + waiting + ' more can be brought in' : '');
    }

    function drawNode(node) {
      const a = svgEl('a', {
        class: 'ww-node ww-' + node.kind + (node.kind === 'piece' && node.total === 1 ? ' ww-piece--single' : ''),
        href: node.kind === 'word' ? '?word=' + encodeURIComponent(node.entry.id) : '?piece=' + encodeURIComponent(node.key),
      });
      a.appendChild(svgEl('title', {}, describe(node)));
      if (node.kind === 'word') {
        a.appendChild(svgEl('rect', { x: -node.hw, y: -node.hh, width: 2 * node.hw, height: 2 * node.hh, rx: 11 }));
        a.appendChild(svgEl('text', { class: 'ww-t-word', y: node.gloss ? -3 : 5, lang: 'x-paw' }, node.label));
        if (node.gloss) a.appendChild(svgEl('text', { class: 'ww-t-gloss', y: 13 }, node.gloss));
      } else {
        a.appendChild(svgEl('ellipse', {}));
        a.appendChild(svgEl('text', { class: 'ww-t-piece', y: node.countLabel ? -1 : 5, lang: 'x-paw' }, node.label));
        if (node.countLabel) a.appendChild(svgEl('text', { class: 'ww-t-count', y: 13 }, node.countLabel));
        const badge = svgEl('g', { class: 'ww-more' });
        badge.appendChild(svgEl('circle', { r: 8 }));
        badge.appendChild(svgEl('text', { y: 4 }, '+'));
        a.appendChild(badge);
        node.resized = true;
      }
      node.el = a;
      a.wwNode = node;
      nodeLayer.appendChild(a);
    }

    function sync() {
      sizes(pic, measure);
      pic.nodes.forEach(node => {
        if (!node.el) drawNode(node);
        if (node.kind === 'piece' && node.resized) {            // an oval that gained words has grown
          const oval = node.el.querySelector('ellipse');
          oval.setAttribute('rx', node.hw.toFixed(1));
          oval.setAttribute('ry', node.hh.toFixed(1));
          node.el.querySelector('.ww-more').setAttribute('transform',
            `translate(${(node.hw * 0.82).toFixed(1)},${(-node.hh * 0.82).toFixed(1)})`);
          node.resized = false;
        }
      });
      pic.links.forEach(link => {
        if (!link.el) {
          link.el = svgEl('line', { class: 'ww-link' });
          linkLayer.appendChild(link.el);
        }
      });
      marks();
    }

    /** Which shapes are chosen, which ovals have words waiting, which lines belong to the chosen shape. */
    function marks() {
      pic.nodes.forEach(node => {
        node.el.classList.toggle('ww-node--on', node === selected);
        if (node.kind === 'piece') {
          node.el.classList.toggle('ww-piece--more', pic.hidden(node.key) > 0);
          node.el.querySelector('title').textContent = describe(node);
        }
      });
      pic.links.forEach(link => link.el.classList.toggle('ww-link--on', link.word === selected || link.piece === selected));
    }

    function paint() {
      pic.nodes.forEach(node => node.el.setAttribute('transform', `translate(${node.x.toFixed(1)},${node.y.toFixed(1)})`));
      pic.links.forEach(link => {
        link.el.setAttribute('x1', link.word.x.toFixed(1)); link.el.setAttribute('y1', link.word.y.toFixed(1));
        link.el.setAttribute('x2', link.piece.x.toFixed(1)); link.el.setAttribute('y2', link.piece.y.toFixed(1));
      });
      world.setAttribute('transform', `translate(${view.x.toFixed(1)},${view.y.toFixed(1)}) scale(${view.k.toFixed(4)})`);
    }

    function stage() {
      const s = { w: svg.clientWidth || 900, h: svg.clientHeight || 600 };
      pic.aspect = s.w / s.h;
      return s;
    }

    /** The view that shows the whole picture; when that would make the letters too small, the chosen shape instead. */
    function fitTarget() {
      const b = bounds(pic.nodes), s = stage();
      const k = Math.min(MAX_FIT, (s.w - 28) / Math.max(b.w, 1), (s.h - 28) / Math.max(b.h, 1));
      if (k >= MIN_FIT || !pic.nodes.length) return { k, x: s.w / 2 - k * (b.x + b.w / 2), y: s.h / 2 - k * (b.y + b.h / 2) };
      let focus = selected;
      if (!focus) pic.nodes.forEach(node => { if (node.kind === 'piece' && (!focus || node.deg > focus.deg)) focus = node; });
      return { k: MIN_FIT, x: s.w / 2 - MIN_FIT * focus.x, y: s.h / 2 - MIN_FIT * focus.y };
    }

    /** Ask for the next step of the motion. A browser that gives no animation frames (a tab in the background)
        is not waited for: a timer takes the step instead, so the picture always comes to rest. */
    function schedule() {
      if (frame) return;
      let taken = false;
      const run = () => {
        if (taken) return;
        taken = true;
        window.clearTimeout(timer);
        loop();
      };
      const timer = window.setTimeout(run, 60);
      frame = 1;
      window.requestAnimationFrame(run);
    }

    function loop() {
      frame = 0;
      for (let n = 0; n < 3; n++) { step(pic, alpha); alpha *= 0.982; }
      let moving = alpha > 0.04;
      if (autoFit) {
        const t = fitTarget();
        view.k += (t.k - view.k) * 0.14; view.x += (t.x - view.x) * 0.14; view.y += (t.y - view.y) * 0.14;
        if (Math.abs(t.x - view.x) + Math.abs(t.y - view.y) > 0.6 || Math.abs(t.k - view.k) > 0.002) moving = true;
      }
      if (!moving) tidy(pic);
      paint();
      if (moving) schedule();
    }

    /** Let the picture find its places again after something was added or moved. */
    function heat(amount) {
      if (still) {
        settle(pic, 140, amount);
        if (autoFit) Object.assign(view, fitTarget());
        paint();
        return;
      }
      alpha = Math.max(alpha, amount);
      schedule();
    }

    // ---- the panel under the picture
    function wordRow(entry, highlight) {
      return `<li class="family-item">
        <div class="family-head"><a class="family-word" lang="x-paw" href="${esc(entryLink(entry.id))}">${esc(entry.w)}</a>
          ${entry.cls ? `<span class="gram-class">${esc(entry.cls)}</span>` : ''}
          <span class="family-gloss">${esc(entry.g)}</span></div>
        <div class="family-build">${pieceChips({ u: entry.u, k: entry.k, words: entry.words }, { link: '?piece=', highlight })}
          ${entry.lit ? `<span class="family-lit">“${literalHtml(entry.lit, data.labels)}”</span>` : ''}
          ${entry.unsure ? '<span class="result-usage">(Parks is not sure)</span>' : ''}</div>
      </li>`;
    }

    function spelledLike(key) {
      const heads = data.heads[key.replace(/\./g, '')] || [];
      if (!heads.length) return '';
      return `<details class="learn-details"><summary>${heads.length === 1 ? 'One dictionary entry is' : heads.length + ' dictionary entries are'} spelled like this piece</summary>
        <ul class="spelled-list">${heads.map(h =>
          `<li><a lang="x-paw" class="family-word" href="${esc(entryLink(h.id))}">${esc(h.w)}</a>
           ${h.cls ? `<span class="gram-class">${esc(h.cls)}</span>` : ''} ${esc(h.g)}</li>`).join('')}</ul>
        <p class="result-usage">The dictionary does not say which entry a piece is. Compare these meanings with the words round the oval.</p>
      </details>`;
    }

    function showPanel() {
      if (!selected) {
        panel.innerHTML = '<p class="result-usage">Choose a box to read the word in full, or an oval to bring in more of its words.</p>';
        return;
      }
      if (selected.kind === 'word') {
        const e = selected.entry;
        panel.innerHTML = `<h4 class="family-title">The word you chose</h4>
          <ol class="family-list">${wordRow(e, null)}</ol>
          <p class="ww-actions">
            <a role="button" class="outline secondary ww-btn" href="?word=${encodeURIComponent(e.id)}">A new picture from this word</a>
            <a class="ww-btn-link" href="${esc(entryLink(e.id))}">The dictionary entry</a></p>`;
        return;
      }
      const key = selected.key, all = selected.total, waiting = pic.hidden(key);
      const here = pic.links.filter(l => l.piece === selected).map(l => l.word.entry);
      const full = pic.words.size >= SETTINGS.maxWords;
      panel.innerHTML = `<h4 class="family-title"><span class="piece piece--on" lang="x-paw">${esc(key)}</span>
          is printed in ${all} ${all === 1 ? 'word' : 'words'}${waiting ? `; ${here.length} ${here.length === 1 ? 'is' : 'are'} in the picture` : ''}</h4>
        <p class="ww-actions">
          ${waiting && !full ? `<button type="button" class="outline ww-btn" id="ww-more">Bring in ${Math.min(waiting, SETTINGS.step)} more</button>` : ''}
          ${waiting && full ? '<span class="result-usage">The picture is full. Start a new one from this piece to see its other words.</span>' : ''}
          <a role="button" class="outline secondary ww-btn" href="?piece=${encodeURIComponent(key)}">A new picture from this piece</a>
          <a class="ww-btn-link" href="words.html?piece=${encodeURIComponent(key)}">${all === 1 ? 'The word' : 'All ' + all + ' words'} as a list</a></p>
        ${spelledLike(key)}
        <ol class="family-list">${here.map(e => wordRow(e, key)).join('')}</ol>`;
      const more = document.getElementById('ww-more');
      if (more) more.addEventListener('click', () => choose(selected));
    }

    function showSummary() {
      const drawn = pic.words.size;
      let text = '';
      if (!state) text = '';
      else if (state.kind === 'piece') {
        text = `<span class="piece" lang="x-paw">${esc(state.key)}</span> is printed in ${state.total} ${state.total === 1 ? 'word' : 'words'}.` +
          (pic.hidden(state.key) ? ` ${state.total - pic.hidden(state.key)} of them are drawn; choose the oval to bring in more.` : '');
      } else if (state.kind === 'word') {
        const e = data.entries[state.i];
        text = `<span lang="x-paw" class="result-skiri">${esc(e.w)}</span> “${esc(glossLabel(e))}”, with words that share its pieces.`;
      } else {
        const n = state.found.length;
        text = `${n} ${n === 1 ? 'word has' : 'words have'} “${esc(state.text)}” in the meaning or in the literal translation.` +
          (state.best ? ` The piece <span class="piece" lang="x-paw">${esc(state.best)}</span> is printed in ${state.bestCount} of them.` : '') +
          (state.drawn < n ? ` ${state.drawn} are drawn, those that share the most pieces.
             <button type="button" class="outline ww-btn" id="ww-next">Draw ${Math.min(SETTINGS.queryWords, n - state.drawn)} more</button>` : '');
      }
      summary.innerHTML = text + (drawn >= SETTINGS.maxWords ? ' The picture is full.' : '');
      const next = document.getElementById('ww-next');
      if (next) next.addEventListener('click', () => {
        pic.more(state);
        sync();
        heat(0.9);
        showSummary();
      });
    }

    // ---- choosing and starting
    function choose(node) {
      selected = node;
      if (node.kind === 'piece' && pic.hidden(node.key) > 0 && pic.expand(node.key)) {
        sync();
        heat(0.85);
        showSummary();
      }
      marks();
      showPanel();
    }

    function begin(started, params) {
      if (!started) return false;
      state = started;
      selected = null;
      nodeLayer.textContent = '';
      linkLayer.textContent = '';
      sync();
      stage();
      settle(pic, 320, 1);
      autoFit = true;
      Object.assign(view, fitTarget());
      alpha = 0;
      if (state.kind === 'piece') selected = pic.pieces.get(state.key);
      if (state.kind === 'word') selected = pic.words.get(state.i);
      marks();
      paint();
      showSummary();
      showPanel();
      const url = new URL(window.location.href);
      ['piece', 'q', 'word'].forEach(name => url.searchParams.delete(name));
      Object.keys(params).forEach(name => url.searchParams.set(name, params[name]));
      window.history.replaceState({}, '', url);
      return true;
    }

    const startPiece = key => begin(pic.startPiece(key), { piece: key });
    const startEnglish = text => begin(pic.startEnglish(text), { q: text.trim() });
    const startWord = id => index.byId.has(id) && begin(pic.startWord(index.byId.get(id)), { word: id });

    /** What the visitor typed: a piece if the dictionary prints one with these letters, an English word otherwise. */
    function find(text) {
      const raw = String(text || '').trim();
      if (!raw) return;
      if (startPiece(plainKey(raw)) || (raw.length > 1 && startEnglish(raw))) return;
      summary.innerHTML = `Nothing found for “${esc(raw)}”. Type an English word (<em>bear</em>, <em>black</em>) or a piece in the
        dictionary's letters (<span lang="x-paw">kuruks</span>, <span lang="x-paw">kaatiit</span>).`;
    }

    /** A link of this page (?piece=, ?q=, ?word=) is followed without loading the page again. */
    function follow(href) {
      const params = new URL(href, window.location.href).searchParams;
      if (params.get('piece')) return startPiece(params.get('piece'));
      if (params.get('word')) return startWord(params.get('word'));
      if (params.get('q')) return startEnglish(params.get('q'));
      return false;
    }

    // ---- moving things
    const pointers = new Map();
    let drag = null, pinch = null, moved = false;

    function toWorld(event) {
      const box = svg.getBoundingClientRect();
      return { x: (event.clientX - box.left - view.x) / view.k, y: (event.clientY - box.top - view.y) / view.k };
    }

    function zoomAt(factor, cx, cy) {
      const k = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, view.k * factor));
      view.x = cx - (cx - view.x) * (k / view.k);
      view.y = cy - (cy - view.y) * (k / view.k);
      view.k = k;
      autoFit = false;
      paint();
    }

    function onMove(event) {
      if (!pointers.has(event.pointerId)) return;
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pinch && pointers.size === 2) {
        const [p, q] = Array.from(pointers.values());
        const box = svg.getBoundingClientRect();
        const gap = Math.hypot(p.x - q.x, p.y - q.y) || 1;
        zoomAt(gap / pinch.gap, (p.x + q.x) / 2 - box.left, (p.y + q.y) / 2 - box.top);
        pinch.gap = gap;
        moved = true;
        return;
      }
      if (!drag) return;
      if (Math.hypot(event.clientX - drag.x0, event.clientY - drag.y0) > 4) moved = true;
      if (!moved) return;
      if (drag.node) {
        const at = toWorld(event);
        drag.node.x = at.x + drag.dx;
        drag.node.y = at.y + drag.dy;
        drag.node.fixed = true;
        if (still) paint(); else heat(0.25);
      } else {
        view.x = drag.vx + event.clientX - drag.x0;
        view.y = drag.vy + event.clientY - drag.y0;
        autoFit = false;
        paint();
      }
    }

    function onUp(event) {
      pointers.delete(event.pointerId);
      if (pointers.size < 2) pinch = null;
      if (pointers.size) return;
      if (drag && drag.node) {
        drag.node.fixed = false;
        if (still && moved) heat(0.3);
      }
      drag = null;
      window.setTimeout(() => { moved = false; }, 0);      // the click that ends a drag has been passed over by then
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('pointercancel', onUp);
    }

    svg.addEventListener('pointerdown', event => {
      if (event.button) return;
      if (!pointers.size) {
        moved = false;
        window.addEventListener('pointermove', onMove);
        window.addEventListener('pointerup', onUp);
        window.addEventListener('pointercancel', onUp);
      }
      pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (pointers.size === 2) {
        const [p, q] = Array.from(pointers.values());
        pinch = { gap: Math.hypot(p.x - q.x, p.y - q.y) || 1 };
        if (drag && drag.node) drag.node.fixed = false;
        drag = null;
        return;
      }
      const link = event.target.closest ? event.target.closest('.ww-node') : null;
      const at = toWorld(event);
      drag = link
        ? { node: link.wwNode, x0: event.clientX, y0: event.clientY, dx: link.wwNode.x - at.x, dy: link.wwNode.y - at.y }
        : { x0: event.clientX, y0: event.clientY, vx: view.x, vy: view.y };
    });

    // A shape is a link, so it can be reached with the keyboard and opened in a new tab; an ordinary click stays here.
    svg.addEventListener('click', event => {
      const link = event.target.closest ? event.target.closest('.ww-node') : null;
      if (!link) return;
      if (moved) { event.preventDefault(); return; }
      if (event.ctrlKey || event.metaKey || event.shiftKey) return;
      event.preventDefault();
      choose(link.wwNode);
    });
    svg.addEventListener('dragstart', event => event.preventDefault());
    svg.addEventListener('wheel', event => {
      if (!event.ctrlKey && !event.metaKey) return;          // an ordinary wheel scrolls the page
      event.preventDefault();
      const box = svg.getBoundingClientRect();
      zoomAt(event.deltaY < 0 ? 1.12 : 1 / 1.12, event.clientX - box.left, event.clientY - box.top);
    }, { passive: false });

    document.getElementById('ww-in').addEventListener('click', () => { const s = stage(); zoomAt(1.25, s.w / 2, s.h / 2); });
    document.getElementById('ww-out').addEventListener('click', () => { const s = stage(); zoomAt(1 / 1.25, s.w / 2, s.h / 2); });
    document.getElementById('ww-fit').addEventListener('click', () => {
      autoFit = true;
      const s = stage(), b = bounds(pic.nodes);
      const k = Math.min(MAX_FIT, (s.w - 28) / Math.max(b.w, 1), (s.h - 28) / Math.max(b.h, 1));     // the whole of it, however small
      Object.assign(view, { k, x: s.w / 2 - k * (b.x + b.w / 2), y: s.h / 2 - k * (b.y + b.h / 2) });
      autoFit = k >= MIN_FIT;
      paint();
    });
    window.addEventListener('resize', () => { if (autoFit) { Object.assign(view, fitTarget()); paint(); } });

    // ---- the box to type in, the words to start from, the links of the panel
    let timer = null;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => find(input.value), 450);
    });
    document.getElementById('ww-form').addEventListener('submit', event => {
      event.preventDefault();
      clearTimeout(timer);
      find(input.value);
    });
    document.querySelectorAll('.ww .key-btn[data-insert]').forEach(btn => btn.addEventListener('click', () => {
      const at = input.selectionStart == null ? input.value.length : input.selectionStart;
      input.value = input.value.slice(0, at) + btn.dataset.insert + input.value.slice(input.selectionEnd == null ? at : input.selectionEnd);
      input.focus();
      find(input.value);
    }));
    document.querySelector('.ww').addEventListener('click', event => {
      const link = event.target.closest('a.ww-start, a.piece, a.ww-btn');
      if (!link || event.ctrlKey || event.metaKey || event.shiftKey) return;
      const href = link.getAttribute('href') || '';
      if (!href.startsWith('?')) return;
      event.preventDefault();
      const params = new URLSearchParams(href.slice(1));
      input.value = params.get('q') || params.get('piece') || '';
      if (follow(href)) svg.scrollIntoView({ behavior: still ? 'auto' : 'smooth', block: 'nearest' });
    });

    const first = new URLSearchParams(window.location.search);
    const asked = first.get('piece') || first.get('q') || first.get('word');
    if (!follow(window.location.href)) {
      startEnglish(svg.dataset.start || 'bear');
      if (asked) {
        summary.innerHTML = `Nothing to draw for “${esc(asked)}”: the dictionary prints no derivation in two or more
          pieces under that name. Here are the words with “${esc(svg.dataset.start || 'bear')}” instead.`;
      }
    } else {
      input.value = first.get('q') || first.get('piece') || '';
    }
  }

  if (typeof document !== 'undefined' && document.addEventListener) {
    document.addEventListener('DOMContentLoaded', () => { if (document.getElementById('ww-svg')) mount(); });
  }

  return { SETTINGS, plainKey, englishPattern, makeIndex, wordLabel, glossLabel, createPicture, sizes, step, settle, tidy, overlaps, bounds };
})();
