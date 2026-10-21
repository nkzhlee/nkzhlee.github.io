document.documentElement.classList.add('js');

const nav = document.querySelector('.site-header nav');
if (nav) {
  nav.id = 'primary-nav';
  const toggle = document.createElement('button');
  toggle.className = 'menu-toggle';
  toggle.type = 'button';
  toggle.textContent = 'Menu';
  toggle.setAttribute('aria-controls', 'primary-nav');
  toggle.setAttribute('aria-expanded', 'false');
  nav.before(toggle);
  const closeMenu = () => {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.textContent = 'Menu';
  };
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Close' : 'Menu';
  });
  nav.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav.classList.contains('is-open')) {
      closeMenu();
      toggle.focus();
    }
  });
}

const news = document.querySelector('#recent-news');
if (news) {
  const toggle = news.querySelector('.news-toggle');
  const moreLabel = toggle.textContent;
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    const expanded = news.classList.toggle('is-expanded');
    toggle.setAttribute('aria-expanded', String(expanded));
    toggle.textContent = expanded ? 'Show less' : moreLabel;
  });
}

const search = document.querySelector('#publication-search');
if (search) {
  const type = document.querySelector('#publication-type');
  const year = document.querySelector('#publication-year');
  const records = [...document.querySelectorAll('[data-publication]')];
  const groups = [...document.querySelectorAll('[data-publication-group]')];
  const count = document.querySelector('#publication-count');
  const noResults = document.querySelector('#no-results');
  const citationSection = document.querySelector('#publication-list');
  const citationDisclosure = search.closest('.publication-list-disclosure');
  const normalize = (value) => value.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  function filter() {
    const terms = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const record of records) {
      const matches = terms.every(term => normalize(record.dataset.search).includes(term))
        && (!type.value || record.dataset.type === type.value)
        && (!year.value || record.dataset.year === year.value);
      record.hidden = !matches;
      shown += Number(matches);
    }
    for (const group of groups) {
      group.hidden = ![...group.querySelectorAll('[data-publication]')].some(record => !record.hidden);
      if (!group.hidden && (terms.length || type.value || year.value)) group.open = true;
    }
    count.textContent = shown + (shown === 1 ? ' result' : ' results') + ' of ' + records.length;
    noResults.hidden = shown !== 0;
  }
  search.addEventListener('input', filter);
  type.addEventListener('change', filter);
  year.addEventListener('change', filter);
  function resetFilters() {
    search.value = ''; type.value = ''; year.value = ''; filter();
  }
  document.querySelector('#reset-filters').addEventListener('click', () => {
    resetFilters(); search.focus();
  });
  document.querySelectorAll('[data-publication-jump]').forEach(link => {
    link.addEventListener('click', resetFilters);
  });
  function revealPublicationTarget(target) {
    if (!target || !citationSection?.contains(target)) return false;
    if (citationDisclosure) citationDisclosure.open = true;
    const record = target.closest('[data-publication]');
    const group = target.closest('[data-publication-group]');
    if (record?.hidden || group?.hidden) resetFilters();
    if (group) group.open = true;
    return true;
  }
  function hashTarget(hash) {
    try { return document.getElementById(decodeURIComponent(hash.slice(1))); }
    catch (_) { return null; }
  }
  function revealPublicationHash() {
    const target = hashTarget(location.hash);
    if (revealPublicationTarget(target)) {
      requestAnimationFrame(() => target.scrollIntoView({block: 'start', behavior: 'auto'}));
    }
  }
  // Open before anchor scrolling or the map result handler moves focus.
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (link) revealPublicationTarget(hashTarget(link.getAttribute('href')));
  }, true);
  window.addEventListener('hashchange', revealPublicationHash);
  filter();
  revealPublicationHash();
}
