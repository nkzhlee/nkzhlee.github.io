/* The map owns only its result panel; existing publication filters stay independent. */
(() => {
  const map = document.querySelector('[data-publication-map]');
  if (!map) return;
  const disclosure = map.closest('details');
  function revealHashTarget() {
    if (!disclosure || !location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (target && (target === map || map.contains(target))) {
      disclosure.open = true;
      requestAnimationFrame(() => target.scrollIntoView({block: 'start', behavior: 'auto'}));
    }
  }
  revealHashTarget();
  window.addEventListener('hashchange', revealHashTarget);
  const dataElement = map.querySelector('[data-map-data]');
  if (!dataElement) return;
  let data;
  try { data = JSON.parse(dataElement.textContent); } catch (_) { return; }
  const communities = new Map(data.communities.map(c => [c.id, c]));
  const venues = new Map(data.venues.map(v => [v.id, v]));
  const topics = new Map(data.topics.map(t => [t.id, t]));
  const results = map.querySelector('#map-results');
  const list = map.querySelector('[data-map-result-list]');
  const heading = map.querySelector('[data-map-result-title]');
  const status = map.querySelector('[data-map-status]');
  const buttons = [...map.querySelectorAll('[data-map-select]')];
  const rows = [...map.querySelectorAll('[data-map-row]')];
  let previousButton = null;

  function key(button) {
    return ['mapCommunity', 'mapVenue', 'mapTopic'].map(k => button.dataset[k] || '').join('|');
  }

  function clear() {
    results.hidden = true;
    map.classList.remove('has-map-selection');
    buttons.forEach(button => button.setAttribute('aria-pressed', 'false'));
    rows.forEach(row => row.classList.remove('is-muted'));
    list.replaceChildren();
    map.dispatchEvent(new CustomEvent('publication-map:select', {bubbles: true, detail: {
      ids: data.records.map(record => record.id), label: '', active: false
    }}));
    if (previousButton) previousButton.focus({preventScroll: true});
  }

  function select(button) {
    const communityId = button.dataset.mapCommunity;
    const venueId = button.dataset.mapVenue;
    const topicId = button.dataset.mapTopic;
    const selected = data.records.filter(record =>
      (!communityId || record.communityId === communityId) &&
      (!venueId || record.venueId === venueId) &&
      (!topicId || record.topicIds.includes(topicId))
    );
    const label = [communityId && `${communities.get(communityId).label} — venue grouping`,
      venueId && venues.get(venueId).label, topicId && topics.get(topicId).label].filter(Boolean).join(' × ');
    const ids = new Set(selected.map(record => record.id));
    const selectedVenues = new Set(selected.map(record => record.venueId));
    const selectionKey = key(button);
    map.classList.add('has-map-selection');
    buttons.forEach(item => item.setAttribute('aria-pressed', String(key(item) === selectionKey)));
    rows.forEach(row => row.classList.toggle('is-muted', !selectedVenues.has(row.dataset.mapRow)));
    previousButton = button;
    heading.textContent = label;
    list.replaceChildren();
    // Preserve the CV's order rather than sorting undated records artificially.
    for (const publication of data.publications.filter(p => ids.has(p.id))) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = '#' + encodeURIComponent(publication.id);
      link.textContent = publication.title;
      const metadata = document.createElement('span');
      metadata.textContent = [publication.year || 'Undated', publication.type].filter(Boolean).join(' · ');
      item.append(link, metadata);
      list.append(item);
    }
    results.hidden = false;
    status.textContent = `${selected.length} ${selected.length === 1 ? 'work' : 'works'}${communityId ? ' in this venue grouping, not a total for the research topic' : ''}. Select a title to jump to its full citation.`;
    map.dispatchEvent(new CustomEvent('publication-map:select', {bubbles: true, detail: {
      ids: [...ids], label, active: true
    }}));
    results.scrollIntoView({block: 'nearest', behavior: 'auto'});
  }

  map.addEventListener('click', event => {
    const button = event.target.closest('[data-map-select]');
    if (button && map.contains(button)) select(button);
    if (event.target.closest('[data-map-clear]')) clear();
  });

  list.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link) return;
    const target = document.getElementById(decodeURIComponent(link.hash.slice(1)));
    if (!target) return;
    // A previous search may hide the target. Reset existing filters first.
    if (target.hidden) document.querySelector('#reset-filters')?.click();
    target.setAttribute('tabindex', '-1');
    target.focus({preventScroll: true});
  });
})();
