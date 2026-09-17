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

const search = document.querySelector('#publication-search');
if (search) {
  const type = document.querySelector('#publication-type');
  const year = document.querySelector('#publication-year');
  const records = [...document.querySelectorAll('[data-publication]')];
  const count = document.querySelector('#publication-count');
  const noResults = document.querySelector('#no-results');
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
    count.textContent = shown + (shown === 1 ? ' result' : ' results') + ' of ' + records.length;
    noResults.hidden = shown !== 0;
  }
  search.addEventListener('input', filter);
  type.addEventListener('change', filter);
  year.addEventListener('change', filter);
  document.querySelector('#reset-filters').addEventListener('click', () => {
    search.value = ''; type.value = ''; year.value = ''; filter(); search.focus();
  });
  filter();
}
