/**
 * "Sound it out" on the Sounds page: a flashcard word, with the phonetic form Parks prints
 * for it cut at its syllable dots and each sound explained (Skiri.soundItOut, skiri.js).
 * Data: data/practice.json. Words without a printed phonetic form are not offered.
 */
(() => {
  const { esc, soundItOut, entryLink, load } = Skiri;
  let weeks = [];

  function words(weekNumber) {
    const week = weeks.find(w => String(w.week) === String(weekNumber));
    return week ? week.cards : [];
  }

  function show(card) {
    const out = document.getElementById('so-out');
    if (!card) { out.innerHTML = ''; return; }
    out.innerHTML = `<div class="sound-card">
        <div class="sound-card-head"><span class="q-word" lang="x-paw">${Skiri.spell(card.p || card.w, card.p ? card.w : '')}</span>
          ${card.p ? `<span class="secondary-spelling" lang="x-paw">${Skiri.spellOther(card.p || card.w, card.w)}</span>` : ''}
          <span class="family-gloss">${esc(card.def)}</span></div>
        <p class="result-ipa" lang="x-paw">${esc(card.ipa)}</p>
        ${soundItOut(card.ipa, card.say)}
        <p class="result-usage"><a href="${esc(entryLink(card.id))}">The dictionary entry</a></p>
      </div>`;
  }

  function fillWords(weekNumber, chosenId) {
    const select = document.getElementById('so-word');
    const cards = words(weekNumber);
    select.innerHTML = cards.map(c => `<option value="${esc(c.id)}">${esc(c.w)} — ${esc(c.def)}</option>`).join('');
    if (chosenId) select.value = chosenId;
    show(cards.find(c => c.id === select.value) || cards[0]);
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const out = document.getElementById('so-out');
    if (!out) return;
    try {
      const data = await load('practice');
      weeks = data.weeks.map(w => ({ week: w.week, label: w.label, cards: w.cards.filter(c => c.ipa) })).filter(w => w.cards.length);
    } catch (error) {
      out.innerHTML = '<p class="result-usage">The word list could not be loaded.</p>';
      return;
    }
    const weekSelect = document.getElementById('so-week');
    weekSelect.innerHTML = weeks.map(w => `<option value="${w.week}">Week ${w.week}: ${esc(w.label)}</option>`).join('');
    // open on a week of dictionary words: the first weeks are textbook words, most without a phonetic form
    const start = weeks.find(w => w.cards.length >= 10) || weeks[0];
    weekSelect.value = String(start.week);
    fillWords(start.week);

    weekSelect.addEventListener('change', () => fillWords(weekSelect.value));
    document.getElementById('so-word').addEventListener('change', e => {
      show(words(weekSelect.value).find(c => c.id === e.target.value));
    });
    document.getElementById('so-random').addEventListener('click', () => {
      const week = weeks[Math.floor(Math.random() * weeks.length)];
      const card = week.cards[Math.floor(Math.random() * week.cards.length)];
      weekSelect.value = String(week.week);
      fillWords(week.week, card.id);
    });
  });
})();
